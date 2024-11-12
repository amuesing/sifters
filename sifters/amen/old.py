import mido
import music21
import numpy as np

# Global Configuration
title = 'amen'
output_dir = 'sifters/amen/mid/'
ticks_per_quarter_note = 480
duration = ticks_per_quarter_note // 4  # 16th note duration

# Instrument Configuration
instrument_dict = {
    'snare': {
        'sieve': '5@2|6@3|8@4',
        'accent_dict': {'primary': '5@1', 'secondary': '4@2'},
        'velocity_profile': {'gap': 50, 'primary': 100, 'secondary': 80, 'overlap': 120},
        'note': 38  # MIDI Note for snare drum
    },
    'kick': {
        'sieve': '8@2|9@2|10@0',
        'note': 36  # MIDI Note for kick drum
    }
}

# Utility Functions
def sieve_to_binary(sieve):
    return np.array(sieve.segment(segmentFormat='binary'))

def shift_binary(binary, shift_amount):
    return np.roll(binary, shift_amount)

def invert_binary(binary):
    return 1 - binary

def reverse_binary(binary):
    return binary[::-1]

def stretch_binary(binary, factor):
    return binary.repeat(factor)

# Sieve Processing
def create_sieve_objs(instrument_dict):
    return [(name, music21.sieve.Sieve(info['sieve'])) for name, info in instrument_dict.items()]

def find_largest_period(instrument_dict):
    return max(music21.sieve.Sieve(info['sieve']).period() for info in instrument_dict.values())

def create_accent_binaries(accent_dict, largest_period):
    default_accent_dict = {'primary': '', 'secondary': ''}
    accent_dict = accent_dict or default_accent_dict
    accent_binaries = {}

    for name, sieve_pattern in accent_dict.items():
        if sieve_pattern:
            sieve_obj = music21.sieve.Sieve(sieve_pattern)
            sieve_obj.setZRange(0, largest_period - 1)
            accent_binaries[name] = sieve_to_binary(sieve_obj)
        else:
            accent_binaries[name] = np.zeros(largest_period)

    return accent_binaries

def accent_velocity_with_patterns(binary, primary_binary, secondary_binary, velocity_profile):
    default_velocity_profile = {'gap': 64, 'primary': 94, 'secondary': 64, 'overlap': 32}
    velocity_profile = velocity_profile or default_velocity_profile

    primary_length = len(primary_binary)
    secondary_length = len(secondary_binary)
    velocities = np.zeros(len(binary), dtype=int)

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

def create_midi(binary, period, filename, velocities, note):
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)

    for value, velocity in zip(binary, velocities):
        track.append(mido.Message('note_on', note=note, velocity=velocity if value else 0, time=0))
        track.append(mido.Message('note_off', note=note, velocity=velocity if value else 0, time=duration))

    track.append(mido.MetaMessage('track_name', name=filename))
    track.append(mido.MetaMessage('time_signature', numerator=period, denominator=16, time=0))
    mid.save(f'{output_dir}{filename}.mid')

def process_sieve(sieve, name, period, accent_binaries, velocity_profile, note):
    transformations = {
        'prime': lambda x: x,
        'invert': invert_binary,
        'reverse': reverse_binary,
        'stretch_2': lambda x: stretch_binary(x, 2)
    }

    primary_binary = accent_binaries.get('primary', np.zeros(period))
    secondary_binary = accent_binaries.get('secondary', np.zeros(period))
    base_binary = sieve_to_binary(sieve)

    for suffix, transform in transformations.items():
        transformed_binary = transform(base_binary)
        if not transformed_binary.any():
            continue  # Skip empty transformations

        filename = f'{title}_{name}_{suffix}'
        velocities = accent_velocity_with_patterns(transformed_binary, primary_binary, secondary_binary, velocity_profile)
        create_midi(transformed_binary, period, filename, velocities, note)

    indices = np.nonzero(base_binary)[0]
    for i in indices:
        shifted_binary = shift_binary(base_binary, i)
        filename = f'{title}_{name}_shift_clip{i + 1}'
        velocities = accent_velocity_with_patterns(shifted_binary, primary_binary, secondary_binary, velocity_profile)
        create_midi(shifted_binary, period, filename, velocities, note)

# Main Execution
sieve_objs = create_sieve_objs(instrument_dict)
largest_period = find_largest_period(instrument_dict)

for name, sieve in sieve_objs:
    sieve.setZRange(0, largest_period - 1)
    accent_binaries = create_accent_binaries(instrument_dict[name].get('accent_dict', {}), largest_period)
    velocity_profile = instrument_dict[name].get('velocity_profile', None)
    note = instrument_dict[name].get('note', 64)  # Default to MIDI note 64 if not specified
    process_sieve(sieve, name, largest_period, accent_binaries, velocity_profile, note)