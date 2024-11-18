import os
import mido
import music21
import numpy
import glob

# Global Configuration
title = 'untitled'
output_dir = f'sifters/{title}/mid/'
ticks_per_quarter_note = 480
duration = ticks_per_quarter_note // 4  # 16th note duration
DEFAULT_VELOCITY_PROFILE = {'gap': 64, 'primary': 96, 'secondary': 64, 'overlap': 32}

# Ensure Output Directory Exists
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

def clear_output_directory(output_dir):
    """Delete all contents of the output directory."""
    for file_path in glob.glob(f'{output_dir}*'):
        os.remove(file_path)  # Delete the file

# Clear the output directory at the start of the script
clear_output_directory(output_dir)

# Instrument Configuration
instrument_dict = {
    'snare': {
        'sieve': '(7@0|7@1|7@5)&(5@1|5@3)'
    },
    'clap': {
        'sieve': '(7@5|7@6)&(5@2|5@3|5@4)'
    },
    'kick': {
        'sieve': '(7@0|7@1|7@2)&(5@0)'
    },
    # 'mod5': {
    #     'sieve': '(5@2|5@3)',
    # }
}

# Utility Functions
def sieve_to_binary(sieve):
    return numpy.array(sieve.segment(segmentFormat='binary'))

def shift_binary(binary, shift_amount):
    return numpy.roll(binary, shift_amount)

def invert_binary(binary):
    return 1 - binary

def reverse_binary(binary):
    return binary[::-1]

def stretch_binary(binary, factor):
    return binary.repeat(factor)

def prime_factors(n):
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

def generate_time_signature(period):
    factors = prime_factors(period)
    numerator = max(factors) if factors else 1
    # denominator_options = [1, 2, 4, 7, 16, 32]
    denominator = 16
    return numerator, denominator

def create_midi(binary, period, filename, velocities, note):
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)
    numerator, denominator = generate_time_signature(period)
    track.append(mido.MetaMessage('time_signature', numerator=numerator, denominator=denominator, time=0))

    for value, velocity in zip(binary, velocities):
        track.append(mido.Message('note_on', note=note, velocity=velocity if value else 0, time=0))
        track.append(mido.Message('note_off', note=note, velocity=velocity if value else 0, time=duration))

    track.append(mido.MetaMessage('track_name', name=filename))
    mid.save(f'{output_dir}{filename}.mid')

def create_sieve_objs(instrument_dict):
    return [(name, music21.sieve.Sieve(info['sieve'])) for name, info in instrument_dict.items()]

def find_largest_period(instrument_dict):
    return max(music21.sieve.Sieve(info['sieve']).period() for info in instrument_dict.values())

def create_accent_binaries(accent_dict, largest_period):
    accent_dict = accent_dict or {'primary': '', 'secondary': ''}
    return {
        name: sieve_to_binary(music21.sieve.Sieve(pattern)) if pattern else numpy.zeros(largest_period)
        for name, pattern in accent_dict.items()
    }

def accent_velocity_with_patterns(binary, primary_binary, secondary_binary, velocity_profile):
    primary_length = len(primary_binary)
    secondary_length = len(secondary_binary)
    velocities = numpy.zeros(len(binary), dtype=int)

    for i, value in enumerate(binary):
        if value:
            primary = primary_binary[i % primary_length]
            secondary = secondary_binary[i % secondary_length]
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
    transformations = {
        'prime': lambda x: x,
        # 'invert': invert_binary,
        # 'reverse': reverse_binary,
        # 'stretch_2': lambda x: stretch_binary(x, 2)
    }

    primary_binary = accent_binaries.get('primary', numpy.zeros(period))
    secondary_binary = accent_binaries.get('secondary', numpy.zeros(period))
    base_binary = sieve_to_binary(sieve)

    for suffix, transform in transformations.items():
        transformed_binary = transform(base_binary)
        if not transformed_binary.any():
            continue  # Skip empty transformations

        filename = f'{title}_{name}_{suffix}'
        velocities = accent_velocity_with_patterns(transformed_binary, primary_binary, secondary_binary, velocity_profile)
        create_midi(transformed_binary, period, filename, velocities, note)

    indices = numpy.nonzero(base_binary)[0]
    # for i in indices:
    #     shifted_binary = shift_binary(base_binary, i)
    #     filename = f'{title}_{name}_shift_clip{i}'
    #     velocities = accent_velocity_with_patterns(shifted_binary, primary_binary, secondary_binary, velocity_profile)
    #     create_midi(shifted_binary, period, filename, velocities, note)

# Main Execution
sieve_objs = create_sieve_objs(instrument_dict)
largest_period = find_largest_period(instrument_dict)

for name, sieve in sieve_objs:
    sieve.setZRange(0, largest_period - 1)
    accent_binaries = create_accent_binaries(instrument_dict[name].get('accent_dict', {}), largest_period)
    velocity_profile = instrument_dict[name].get('velocity_profile', DEFAULT_VELOCITY_PROFILE)
    note = instrument_dict[name].get('note', 64)  # Default to MIDI note 64 if not specified
    process_sieve(sieve, name, largest_period, accent_binaries, velocity_profile, note)