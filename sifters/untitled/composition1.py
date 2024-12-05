import os
import mido
import music21
import numpy
import glob

# Global Configuration
TITLE = 'untitled'
OUTPUT_DIR = f'sifters/{TITLE}/mid/'
TICKS_PER_QUARTER_NOTE = 480
DURATION = TICKS_PER_QUARTER_NOTE // 4  # 16th note duration
DEFAULT_VELOCITY_PROFILE = {'gap': 64, 'primary': 96, 'secondary': 64, 'overlap': 32}

# Instrument Configuration

INSTRUMENT_DICT = {
    '(2@0&3@0)': {
        'sieve': '(2@0&3@0)'},
    '(2@0&3@1)': {
        'sieve': '(2@0&3@1)'},
    '(2@0&3@2)': {
        'sieve': '(2@0&3@2)'},
    '(2@1&3@0)': {
        'sieve': '(2@1&3@0)'},
    '(2@1&3@1)': {
        'sieve': '(2@1&3@1)'},
    '(2@1&3@2)': {
        'sieve': '(2@1&3@2)'},
    }



# Utility Functions
def ensure_directory(path):
    '''Ensure a directory exists.'''
    os.makedirs(path, exist_ok=True)

def clear_directory(path):
    '''Delete all files in the specified directory.'''
    for file_path in glob.glob(f'{path}*'):
        os.remove(file_path)

def sieve_to_binary(sieve):
    '''Convert a sieve to its binary representation.'''
    return numpy.array(sieve.segment(segmentFormat='binary'))

def generate_time_signature(period):
    '''Generate a time signature based on the sieve period.'''
    factors = prime_factors(period)
    numerator = max(factors) if factors else 1
    return numerator, 16  # Default denominator: 16

def prime_factors(n):
    '''Find the prime factors of a number.'''
    factors = []
    while n % 2 == 0:
        factors.append(2)
        n //= 2
    factor = 3
    while factor * factor <= n:
        while n % factor == 0:
            factors.append(factor)
            n //= factor
        factor += 2
    if n > 2:
        factors.append(n)
    return factors

def create_midi(binary, period, filename, velocities, note):
    '''Create and save a MIDI file from binary data and velocities.'''
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)

    # Set the track name
    track.append(mido.MetaMessage('track_name', name=filename, time=0))

    # Set the time signature
    numerator, denominator = generate_time_signature(period)
    track.append(mido.MetaMessage('time_signature', numerator=numerator, denominator=denominator, time=0))

    # Add notes
    for value, velocity in zip(binary, velocities):
        track.append(mido.Message('note_on', note=note, velocity=velocity if value else 0, time=0))
        track.append(mido.Message('note_off', note=note, velocity=velocity if value else 0, time=DURATION))

    # Save the MIDI file
    mid.save(f'{OUTPUT_DIR}{filename}.mid')

def create_accent_binaries(accent_dict, period):
    '''Create accent binaries from patterns.'''
    return {
        name: sieve_to_binary(music21.sieve.Sieve(pattern)) if pattern else numpy.zeros(period)
        for name, pattern in (accent_dict or {}).items()
    }

def accent_velocity(binary, primary_binary, secondary_binary, velocity_profile):
    '''Apply velocity patterns based on accent binaries.'''
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
    '''Process a sieve to generate MIDI files.'''
    base_binary = sieve_to_binary(sieve)
    primary_binary = accent_binaries.get('primary', numpy.zeros(period))
    secondary_binary = accent_binaries.get('secondary', numpy.zeros(period))

    # Base transformation
    velocities = accent_velocity(base_binary, primary_binary, secondary_binary, velocity_profile)
    create_midi(base_binary, period, f'{name}_base', velocities, note)

# Main Execution
def main():
    ensure_directory(OUTPUT_DIR)
    clear_directory(OUTPUT_DIR)

    sieve_objs = [(name, music21.sieve.Sieve(info['sieve'])) for name, info in INSTRUMENT_DICT.items()]
    largest_period = max(sieve.period() for _, sieve in sieve_objs)

    for name, sieve in sieve_objs:
        sieve.setZRange(0, largest_period - 1)
        instrument_config = INSTRUMENT_DICT[name]
        accent_binaries = create_accent_binaries(instrument_config.get('accent_dict', {}), largest_period)
        velocity_profile = instrument_config.get('velocity_profile', DEFAULT_VELOCITY_PROFILE)
        note = instrument_config.get('note', 64)  # Default to note 64
        process_sieve(sieve, name, largest_period, accent_binaries, velocity_profile, note)

if __name__ == '__main__':
    main()