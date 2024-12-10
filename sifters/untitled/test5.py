import os
import mido
import music21
import numpy
import glob


# Configuration
TITLE = 'untitled'
OUTPUT_DIR = f'sifters/{TITLE}/mid/'
TICKS_PER_QUARTER_NOTE = 480
DEFAULT_VELOCITY_PROFILE = {'gap': 64, 'primary': 96, 'secondary': 64, 'overlap': 32}
DURATION_MULTIPLIER_KEY = {'Whole Note': 4, 'Half Note': 2, 'Quarter Note': 1, 'Eighth Note': 0.5, 'Sixteenth Note': 0.25}
DURATION_TO_DENOMINATOR = {'Whole Note': 1, 'Half Note': 2, 'Quarter Note': 4, 'Eighth Note': 8, 'Sixteenth Note': 16}

INSTRUMENT_DICT = {
    'snare1': {
        'sieve': '(3@0|3@2)&(4@1|4@3)&(5@3|5@2)',
        'accent_dict': {'primary': '(5@2)', 'secondary': '(5@3)'},
        'duration': 'Sixteenth Note',
        'note': 60,
    },
    'snare2': {
        'sieve': '(3@1|3@2)&(4@0|4@3)&(5@2|5@4)',
        'accent_dict': {'primary': '(5@2)', 'secondary': '(5@4)'},
        'duration': 'Sixteenth Note',
        'note': 60,
    },
    'kick1': {
        'sieve': '(10@0|12@0|15@0)',
        'accent_dict': {'primary': '10@0', 'secondary': '12@0'},
        'duration': 'Sixteenth Note',
        'note': 60,
    },
}

# Utility Functions
def ensure_directory(path):
    os.makedirs(path, exist_ok=True)

def clear_directory(path):
    """Delete all files in the specified directory."""
    for file_path in glob.glob(f'{path}*'):
        os.remove(file_path)

def sieve_to_binary(sieve):
    return numpy.array(sieve.segment(segmentFormat='binary'))

def generate_time_signature(period, duration):
    if period > 255:
        raise ValueError(f"The period {period} exceeds the maximum allowed value of 255.")
    return period, DURATION_TO_DENOMINATOR.get(duration, 16)

def get_duration_multiplier(note_name):
    return DURATION_MULTIPLIER_KEY.get(note_name, 0.25)

def create_midi(binary, filename, velocities, note, duration_multiplier, time_signature):
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.MetaMessage('track_name', name=filename, time=0))
    numerator, denominator = time_signature
    track.append(mido.MetaMessage('time_signature', numerator=numerator, denominator=denominator, time=0))
    duration_ticks = int(TICKS_PER_QUARTER_NOTE * duration_multiplier)
    
    for value, velocity in zip(binary, velocities):
        vel = velocity if value else 0
        track.append(mido.Message('note_on', note=note, velocity=vel, time=0))
        track.append(mido.Message('note_off', note=note, velocity=vel, time=duration_ticks))
    
    mid.save(f'{OUTPUT_DIR}{filename}.mid')

def create_accent_binaries(accent_dict, period):
    return {name: sieve_to_binary(music21.sieve.Sieve(pattern)) if pattern else numpy.zeros(period) for name, pattern in accent_dict.items()}

def accent_velocity(binary, primary, secondary, velocity_profile):
    velocities = numpy.zeros(len(binary), dtype=int)
    for i, value in enumerate(binary):
        if value:
            primary_hit = primary[i % len(primary)]
            secondary_hit = secondary[i % len(secondary)]
            if primary_hit and secondary_hit:
                velocities[i] = velocity_profile['overlap']
            elif primary_hit:
                velocities[i] = velocity_profile['primary']
            elif secondary_hit:
                velocities[i] = velocity_profile['secondary']
            else:
                velocities[i] = velocity_profile['gap']
    return velocities

def process_sieve(name, sieve, period, accent_binaries, velocity_profile, note):
    base_binary = sieve_to_binary(sieve)
    primary_binary = accent_binaries.get('primary', numpy.zeros(period))
    secondary_binary = accent_binaries.get('secondary', numpy.zeros(period))
    velocities = accent_velocity(base_binary, primary_binary, secondary_binary, velocity_profile)
    duration = INSTRUMENT_DICT.get(name, {}).get('duration', 'Quarter Note')
    duration_multiplier = get_duration_multiplier(duration)
    time_signature = generate_time_signature(period, duration)
    
    print(f"Processing {name}: Duration = {duration}, Time Signature = {time_signature}")
    create_midi(base_binary, f'{name}_base', velocities, note, duration_multiplier, time_signature)


def main():
    ensure_directory(OUTPUT_DIR)
    clear_directory(OUTPUT_DIR)  # Clear the output directory before processing
    sieve_objs = [(name, music21.sieve.Sieve(info['sieve'])) for name, info in INSTRUMENT_DICT.items()]
    largest_period = min(max(sieve.period() for _, sieve in sieve_objs), 255)
    
    for name, sieve in sieve_objs:
        sieve.setZRange(0, largest_period - 1)
        config = INSTRUMENT_DICT.get(name, {})
        accent_binaries = create_accent_binaries(config.get('accent_dict', {}), largest_period)
        velocity_profile = config.get('velocity_profile', DEFAULT_VELOCITY_PROFILE)
        note = config.get('note', 64)
        process_sieve(name, sieve, largest_period, accent_binaries, velocity_profile, note)

if __name__ == '__main__':
    main()