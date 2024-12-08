import os
import mido
import music21
import numpy
import glob

# Global Configuration
TITLE = 'untitled'
OUTPUT_DIR = f'sifters/{TITLE}/mid/'
TICKS_PER_QUARTER_NOTE = 480
DEFAULT_VELOCITY_PROFILE = {'gap': 64, 'primary': 96, 'secondary': 64, 'overlap': 32}

# Updated Duration Multiplier Key
DURATION_MULTIPLIER_KEY = {
    'Whole Note': 4,
    'Half Note': 2,
    'Quarter Note': 1,
    'Eighth Note': 0.5,
    'Sixteenth Note': 0.25,
}

# Instrument Configuration
INSTRUMENT_DICT = {
    'complex1': {
        'sieve': '(3@1|3@2)&(4@0|4@3)&(5@2|5@4)',
        'accent_dict': {
            'primary': '(5@2)',
            'secondary': '(5@4)',
        },
        'duration': 'Quarter Note',
    },
    'complex2': {
        'sieve': '(10@0|12@0|15@0)',
        'accent_dict': {
            'primary': '10@0',
            'secondary': '12@0',
        },
        'duration': 'Half Note',
    },
    'complex3': {
        'sieve': '(3@0|3@2)&(4@1|4@3)&(5@3|5@2)',
        'accent_dict': {
            'primary': '(5@2)',
            'secondary': '(5@3)',
        },
        'duration': 'Sixteenth Note',
    },
}

# Utility Functions
def ensure_directory(path):
    """Ensure a directory exists."""
    os.makedirs(path, exist_ok=True)

def clear_directory(path):
    """Delete all files in the specified directory."""
    for file_path in glob.glob(f'{path}*'):
        os.remove(file_path)

def sieve_to_binary(sieve):
    """Convert a sieve to its binary representation."""
    return numpy.array(sieve.segment(segmentFormat='binary'))

def generate_time_signature(period: int, duration: str) -> tuple[int, int]:
    """Generate a time signature with an updated duration dictionary."""
    duration_to_denominator = {
        'Whole Note': 1,
        'Half Note': 2,
        'Quarter Note': 4,
        'Eighth Note': 8,
        'Sixteenth Note': 16,
    }
    denominator = duration_to_denominator.get(duration, 16)  # Default to sixteenth note
    numerator = min(period, 255)  # Cap numerator to 255
    return numerator, denominator

def get_duration_multiplier(note_name: str) -> float:
    """Retrieve the duration multiplier for a given note name."""
    return DURATION_MULTIPLIER_KEY.get(note_name, 0.25)  # Default to sixteenth note multiplier

def create_midi(binary, period, filename, velocities, note, duration_multiplier=1, time_signature=None):
    """Create and save a MIDI file from binary data and velocities."""
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)

    # Set the track name
    track.append(mido.MetaMessage('track_name', name=filename, time=0))

    # Set the time signature
    numerator, denominator = time_signature
    track.append(mido.MetaMessage('time_signature', numerator=numerator, denominator=denominator, time=0))

    # Adjust the duration based on the multiplier
    adjusted_duration = int(TICKS_PER_QUARTER_NOTE * duration_multiplier)

    # Add notes
    for value, velocity in zip(binary, velocities):
        track.append(mido.Message('note_on', note=note, velocity=velocity if value else 0, time=0))
        track.append(mido.Message('note_off', note=note, velocity=velocity if value else 0, time=adjusted_duration))

    # Save the MIDI file
    mid.save(f'{OUTPUT_DIR}{filename}.mid')

def create_accent_binaries(accent_dict, period):
    """Create accent binaries from patterns."""
    return {
        name: sieve_to_binary(music21.sieve.Sieve(pattern)) if pattern else numpy.zeros(period)
        for name, pattern in (accent_dict or {}).items()
    }

def accent_velocity(binary, primary_binary, secondary_binary, velocity_profile):
    """Apply velocity patterns based on accent binaries."""
    primary_len, secondary_len = len(primary_binary), len(secondary_binary)
    velocities = numpy.zeros(len(binary), dtype=int)
    for i, value in enumerate(binary):
        if value:
            primary = primary_binary[i % primary_len]
            secondary = secondary_binary[i % secondary_len]
            if primary and secondary:
                velocities[i] = velocity_profile['overlap']
            elif primary:
                velocities[i] = velocity_profile['primary']
            elif secondary:
                velocities[i] = velocity_profile['secondary']
            else:
                velocities[i] = velocity_profile['gap']
    return velocities

def process_sieve(sieve, name, period, accent_binaries, velocity_profile, note):
    """Process a sieve to generate MIDI files."""
    base_binary = sieve_to_binary(sieve)
    primary_binary = accent_binaries.get('primary', numpy.zeros(period))
    secondary_binary = accent_binaries.get('secondary', numpy.zeros(period))

    # Base transformation
    velocities = accent_velocity(base_binary, primary_binary, secondary_binary, velocity_profile)
    
    # Get the duration from the instrument configuration
    instrument_config = INSTRUMENT_DICT.get(name, {})
    duration_name = instrument_config.get('duration', 'Quarter Note')  # Default to 'Quarter Note'
    duration_multiplier = get_duration_multiplier(duration_name)
    time_signature = generate_time_signature(period, duration_name)
    
    print(f"Processing {name}: Duration = {duration_name} (Multiplier = {duration_multiplier}), Time Signature = {time_signature}")
    
    # Create the MIDI file
    create_midi(base_binary, period, f'{name}_base', velocities, note, duration_multiplier, time_signature)

# Main Execution
def main():
    ensure_directory(OUTPUT_DIR)
    clear_directory(OUTPUT_DIR)

    sieve_objs = [(name, music21.sieve.Sieve(info['sieve'])) for name, info in INSTRUMENT_DICT.items()]
    largest_period = min(max(sieve.period() for _, sieve in sieve_objs), 255)  # Cap period to 255

    for name, sieve in sieve_objs:
        sieve.setZRange(0, largest_period - 1)
        instrument_config = INSTRUMENT_DICT[name]
        accent_binaries = create_accent_binaries(instrument_config.get('accent_dict', {}), largest_period)
        velocity_profile = instrument_config.get('velocity_profile', DEFAULT_VELOCITY_PROFILE)
        note = instrument_config.get('note', 64)  # Default to note 64
        process_sieve(sieve, name, largest_period, accent_binaries, velocity_profile, note)

if __name__ == '__main__':
    main()