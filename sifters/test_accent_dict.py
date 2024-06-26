import mido
import music21
import numpy

title = 'starbird'

sieve_dict = {
    'snare': '(8@0|8@1|8@7)&(5@1|5@3)|((8@0|8@1|8@2)&5@0)|((8@5|8@6)&(5@2|5@3|5@4))',
    'clap': '(((8@0|8@1|8@7)&(5@1|5@3))|((8@0|8@1|8@2)&5@0)|((8@5|8@6)&(5@2|5@3|5@4))|(8@6&5@1)|(8@3)|(8@4)|(8@1&5@2))',
    'kick': '(8@3)|(8@4)',
    'woodblock': '(8@1&5@2)',
    'impact': '(8@6&5@1)'
}

accent_dict = {
    'primary': '8@0|8@1|8@7',
    'secondary': '5@1|5@3',
    'overlap': '(8@0|8@1)&5@0',
    'normal': '(8@0|8@2|8@4|8@6)'
}

def prime_sieve(sieve):
    binary = numpy.array(sieve.segment(segmentFormat='binary'))
    return binary

def shift_sieve(sieve, shift_amount):
    binary = numpy.array(sieve.segment(segmentFormat='binary'))
    shifted_binary = numpy.roll(binary, shift_amount)
    return shifted_binary

def invert_sieve(sieve):
    binary = numpy.array(sieve.segment(segmentFormat='binary'))
    inverted_binary = 1 - binary
    return inverted_binary

def reverse_sieve(sieve):
    binary = numpy.array(sieve.segment(segmentFormat='binary'))
    reversed_binary = binary[::-1]
    return reversed_binary

def stretch_sieve(sieve, factor):
    binary = numpy.array(sieve.segment(segmentFormat='binary'))
    stretched_binary = numpy.repeat(binary, factor)
    return stretched_binary

def create_sieve_objs(sieve_dict):
    sieve_objs = []
    for name, sieve in sieve_dict.items():
        s = music21.sieve.Sieve(sieve)
        sieve_objs.append((name, s))
    return sieve_objs

def find_largest_period(sieve_dict):
    periods = []
    for _, sieve in sieve_dict.items():
        s = music21.sieve.Sieve(sieve)
        period = s.period()
        periods.append(period)
    largest_period = max(periods)
    return largest_period

def create_accent_binaries(accent_dict, period):
    accent_binaries = {}
    for name, sieve in accent_dict.items():
        s = music21.sieve.Sieve(sieve)
        s.setZRange(0, period - 1)
        binary = numpy.array(s.segment(segmentFormat='binary'))
        accent_binaries[name] = binary
    return accent_binaries

def create_midi(binary, period, filename, velocities):
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)

    ticks_per_quarter_note = 480
    duration = ticks_per_quarter_note // 4

    for value, velocity in zip(binary, velocities):
        if value == 0:
            track.append(mido.Message('note_on', note=64, velocity=0, time=0))
            track.append(mido.Message('note_off', note=64, velocity=0, time=duration))
        else:
            track.append(mido.Message('note_on', note=64, velocity=velocity, time=0))
            track.append(mido.Message('note_off', note=64, velocity=velocity, time=duration))

    numerator = period
    denominator = 16
    time_signature = mido.MetaMessage('time_signature', numerator=numerator, denominator=denominator, time=0)
    track.append(mido.MetaMessage('track_name'))
    track.append(time_signature)
    mid.save(f'data/mid/{filename}')

def accent_velocity_with_patterns(binary, accent_binaries, overlap_value=120, primary_value=100, secondary_value=80, normal_value=60):
    velocities = []
    for i, value in enumerate(binary):
        if value == 0:
            velocities.append(0)
        elif accent_binaries['overlap'][i % len(accent_binaries['overlap'])]:
            velocities.append(overlap_value)
        elif accent_binaries['primary'][i % len(accent_binaries['primary'])]:
            velocities.append(primary_value)
        elif accent_binaries['secondary'][i % len(accent_binaries['secondary'])]:
            velocities.append(secondary_value)
        else:
            velocities.append(normal_value)
    return velocities

# Main processing loop
sieve_objs = create_sieve_objs(sieve_dict)
largest_period = find_largest_period(sieve_dict)
accent_binaries = create_accent_binaries(accent_dict, largest_period)

for n, s in sieve_objs:
    s.setZRange(0, largest_period - 1)
    binary = s.segment(segmentFormat='binary')
    indices = numpy.nonzero(binary)[0]

    for i in indices:
        filename = f'{title}_{n}_shift_clip{i + 1}.mid'
        shifted_sieve = shift_sieve(s, i)
        velocities = accent_velocity_with_patterns(shifted_sieve, accent_binaries)
        create_midi(shifted_sieve, largest_period, filename, velocities)

    original_sieve = prime_sieve(s)
    filename = f'{title}_{n}_prime.mid'
    velocities = accent_velocity_with_patterns(original_sieve, accent_binaries)
    create_midi(original_sieve, largest_period, filename, velocities)

    inverted_sieve = invert_sieve(s)
    filename = f'{title}_{n}_invert.mid'
    velocities = accent_velocity_with_patterns(inverted_sieve, accent_binaries)
    create_midi(inverted_sieve, largest_period, filename, velocities)

    reversed_sieve = reverse_sieve(s)
    filename = f'{title}_{n}_reverse.mid'
    velocities = accent_velocity_with_patterns(reversed_sieve, accent_binaries)
    create_midi(reversed_sieve, largest_period, filename, velocities)

    f = 2
    stretched_sieve = stretch_sieve(s, f)
    filename = f'{title}_{n}_stretch_{f}.mid'
    velocities = accent_velocity_with_patterns(stretched_sieve, accent_binaries)
    create_midi(stretched_sieve, largest_period, filename, velocities)