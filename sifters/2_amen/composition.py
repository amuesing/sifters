import mido
import music21
import numpy

title = 'amen'

instrument_dict = {
    # 'hi hat': {
    #     'sieve': '(2@0&-64@58)'
    # },
    # 'crash': {
    #     'sieve': '64@58'
    # },
    'snare': {
        'sieve': '5@2|6@3|8@4'
    }
}

def sieve_to_binary(sieve):
    return numpy.array(sieve.segment(segmentFormat='binary'))

def transform_sieve(sieve, transform, *args):
    binary = sieve_to_binary(sieve)
    transformed_binary = transform(binary, *args)
    return transformed_binary

def shift_binary(binary, shift_amount):
    return numpy.roll(binary, shift_amount)

def invert_binary(binary):
    return 1 - binary

def reverse_binary(binary):
    return binary[::-1]

def stretch_binary(binary, factor):
    return numpy.repeat(binary, factor)

def create_sieve_objs(instrument_dict):
    return [(name, music21.sieve.Sieve(info['sieve'])) for name, info in instrument_dict.items()]

def find_largest_period(instrument_dict):
    return max(music21.sieve.Sieve(info['sieve']).period() for info in instrument_dict.values())

def create_accent_binaries(accent_dict, largest_period):
    accent_binaries = {}
    for name, sieve_pattern in accent_dict.items():
        sieve_obj = music21.sieve.Sieve(sieve_pattern)
        sieve_obj.setZRange(0, largest_period - 1)  # Set the zRange to largest_period
        accent_binaries[name] = sieve_to_binary(sieve_obj)
    return accent_binaries

def create_midi(binary, period, filename, velocities):
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)

    ticks_per_quarter_note = 480
    duration = ticks_per_quarter_note // 4

    for value, velocity in zip(binary, velocities):
        track.append(mido.Message('note_on', note=64, velocity=0 if value == 0 else velocity, time=0))
        track.append(mido.Message('note_off', note=64, velocity=0 if value == 0 else velocity, time=duration))

    time_signature = mido.MetaMessage('time_signature', numerator=period, denominator=16, time=0)
    track.append(mido.MetaMessage('track_name'))
    track.append(time_signature)
    mid.save(f'data/mid/{filename}')

def accent_velocity_with_patterns(binary, primary_binary, secondary_binary, velocity_profile):
    velocities = []

    primary_length = len(primary_binary)
    secondary_length = len(secondary_binary)

    for i, value in enumerate(binary):
        if value == 0:
            velocities.append(0)
        elif primary_binary[i % primary_length] == 1 and secondary_binary[i % secondary_length] == 1:
            velocities.append(velocity_profile['overlap'])
        elif primary_binary[i % primary_length] == 1:
            velocities.append(velocity_profile['primary'])
        elif secondary_binary[i % secondary_length] == 1:
            velocities.append(velocity_profile['secondary'])
        else:
            velocities.append(velocity_profile['gap'])

    return velocities

def create_accent_binaries(accent_dict, largest_period):
    # Set default accent dictionary if none is provided
    if not accent_dict:
        accent_dict = {'primary': '', 'secondary': ''}  # Empty patterns

    accent_binaries = {}
    for name, sieve_pattern in accent_dict.items():
        if sieve_pattern:
            sieve_obj = music21.sieve.Sieve(sieve_pattern)
            sieve_obj.setZRange(0, largest_period - 1)  # Set the zRange to largest_period
            accent_binaries[name] = sieve_to_binary(sieve_obj)
        else:
            accent_binaries[name] = numpy.zeros(largest_period)  # Default to an empty binary
    return accent_binaries

def accent_velocity_with_patterns(binary, primary_binary, secondary_binary, velocity_profile):
    # Set a default velocity profile if none is provided
    default_velocity_profile = {'gap': 64, 'primary': 94, 'secondary': 64, 'overlap': 32}
    velocity_profile = velocity_profile or default_velocity_profile

    velocities = []
    primary_length = len(primary_binary)
    secondary_length = len(secondary_binary)

    for i, value in enumerate(binary):
        if value == 0:
            velocities.append(0)
        elif primary_binary[i % primary_length] == 1 and secondary_binary[i % secondary_length] == 1:
            velocities.append(velocity_profile['overlap'])
        elif primary_binary[i % primary_length] == 1:
            velocities.append(velocity_profile['primary'])
        elif secondary_binary[i % secondary_length] == 1:
            velocities.append(velocity_profile['secondary'])
        else:
            velocities.append(velocity_profile['gap'])

    return velocities

def process_sieve(s, name, period, accent_binaries, velocity_profile):
    # Provide defaults if velocity profile is missing
    velocity_profile = velocity_profile or {'gap': 64, 'primary': 95, 'secondary': 63, 'overlap': 31}
    
    transformations = [
        ('prime', lambda x: x),
        ('invert', invert_binary),
        ('reverse', reverse_binary),
        ('stretch_2', lambda x: stretch_binary(x, 2))
    ]

    primary_binary = accent_binaries.get('primary', numpy.zeros(period))
    secondary_binary = accent_binaries.get('secondary', numpy.zeros(period))

    for suffix, transform in transformations:
        transformed_sieve = transform_sieve(s, transform)
        filename = f'{title}_{name}_{suffix}.mid'
        velocities = accent_velocity_with_patterns(transformed_sieve, primary_binary, secondary_binary, velocity_profile)
        create_midi(transformed_sieve, period, filename, velocities)

    binary = sieve_to_binary(s)
    indices = numpy.nonzero(binary)[0]

    for i in indices:
        filename = f'{title}_{name}_shift_clip{i + 1}.mid'
        shifted_sieve = transform_sieve(s, shift_binary, i)
        velocities = accent_velocity_with_patterns(shifted_sieve, primary_binary, secondary_binary, velocity_profile)
        create_midi(shifted_sieve, period, filename, velocities)

# Main processing loop
sieve_objs = create_sieve_objs(instrument_dict)
largest_period = find_largest_period(instrument_dict)
print(largest_period)

for name, s in sieve_objs:
    s.setZRange(0, largest_period - 1)
    accent_binaries = create_accent_binaries(instrument_dict[name].get('accent_dict', {}), largest_period)
    velocity_profile = instrument_dict[name].get('velocity_profile', None)
    process_sieve(s, name, largest_period, accent_binaries, velocity_profile)