import os
import mido
import music21
import numpy as np

# Global Configuration
CONFIG = {
    'TITLE': 'untitled',
    'OUTPUT_DIR': 'sifters/untitled/mid/',
    'TICKS_PER_QUARTER_NOTE': 480,
    'VELOCITY_PROFILE': {'gap': 64, 'primary': 96, 'secondary': 64, 'overlap': 32},
    'DURATION_MULTIPLIER_KEY': {
        'Whole Note': 4,
        'Half Note': 2,
        'Quarter Note': 1,
        'Eighth Note': 0.5,
        'Sixteenth Note': 0.25,
    },
    'DURATION_DENOMINATOR': {
        'Whole Note': 1,
        'Half Note': 2,
        'Quarter Note': 4,
        'Eighth Note': 8,
        'Sixteenth Note': 16,
    },
    'INSTRUMENTS': {
        'snare1': {
            'sieve': '(3@1|3@2)&(4@0|4@3)&(5@2|5@4)',
            'accent_dict': {'primary': '(5@2)', 'secondary': '(5@4)'},
            'duration': 'Quarter Note',
            'note': 64,
        },
        'snare2': {
            'sieve': '(3@0|3@2)&(4@1|4@3)&(5@3|5@2)',
            'accent_dict': {'primary': '(5@2)', 'secondary': '(5@3)'},
            'duration': 'Sixteenth Note',
            'note': 64,
        },
        'kick1': {
            'sieve': '(10@0|12@0|15@0)',
            'accent_dict': {'primary': '10@0', 'secondary': '12@0'},
            'duration': 'Half Note',
            'note': 36,
        },
    },
}

# Utility Functions
def ensure_directory(path):
    """Ensure a directory exists."""
    os.makedirs(path, exist_ok=True)

def sieve_to_binary(sieve):
    """Convert a sieve to binary representation."""
    return np.array(sieve.segment(segmentFormat='binary'))

def create_midi(binary, filename, velocities, note, duration_multiplier, time_signature):
    """Generate and save a MIDI file."""
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)

    # Set metadata
    track.append(mido.MetaMessage('track_name', name=filename, time=0))
    track.append(mido.MetaMessage('time_signature', numerator=time_signature[0], denominator=time_signature[1], time=0))

    # Set note durations
    adjusted_duration = int(CONFIG['TICKS_PER_QUARTER_NOTE'] * duration_multiplier)

    # Add notes to the track
    for value, velocity in zip(binary, velocities):
        if value:  # Only add notes when the binary value is 1
            track.append(mido.Message('note_on', note=note, velocity=velocity, time=0))
            track.append(mido.Message('note_off', note=note, velocity=0, time=adjusted_duration))

    mid.save(f"{CONFIG['OUTPUT_DIR']}{filename}.mid")

def create_velocities(binary, accent_binaries, velocity_profile):
    """Generate velocities based on binary patterns and accents."""
    primary = accent_binaries.get('primary', [])
    secondary = accent_binaries.get('secondary', [])
    velocities = np.zeros(len(binary), dtype=int)

    for i, value in enumerate(binary):
        if value:
            primary_match = primary[i % len(primary)] if len(primary) > 0 else 0
            secondary_match = secondary[i % len(secondary)] if len(secondary) > 0 else 0
            if primary_match and secondary_match:
                velocities[i] = velocity_profile['overlap']
            elif primary_match:
                velocities[i] = velocity_profile['primary']
            elif secondary_match:
                velocities[i] = velocity_profile['secondary']
            else:
                velocities[i] = velocity_profile['gap']
    return velocities

def process_instrument(name, config):
    """Process a single instrument to create its MIDI file."""
    sieve = music21.sieve.Sieve(config['sieve'])
    period = sieve.period()

    # Set binary patterns
    binary = sieve_to_binary(sieve)
    accent_binaries = {key: sieve_to_binary(music21.sieve.Sieve(val)) for key, val in config.get('accent_dict', {}).items()}

    # Generate velocities
    velocities = create_velocities(binary, accent_binaries, CONFIG['VELOCITY_PROFILE'])

    # Determine duration and time signature
    duration_name = config.get('duration', 'Quarter Note')
    duration_multiplier = CONFIG['DURATION_MULTIPLIER_KEY'].get(duration_name, 0.25)
    time_signature = (period, CONFIG['DURATION_DENOMINATOR'].get(duration_name, 16))

    print(f"Processing {name}: Duration = {duration_name}, Time Signature = {time_signature}")
    create_midi(binary, name, velocities, config.get('note', 64), duration_multiplier, time_signature)

# Main Execution
def main():
    ensure_directory(CONFIG['OUTPUT_DIR'])
    for name, instrument_config in CONFIG['INSTRUMENTS'].items():
        process_instrument(name, instrument_config)

if __name__ == '__main__':
    main()