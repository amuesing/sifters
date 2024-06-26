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

def accent_velocity(binary, primary_modulo, secondary_modulo, overlap_value=120, primary_value=100, secondary_value=80, normal_value=60):
    velocities = []
    for i, value in enumerate(binary):
        if value == 0:
            velocities.append(0)
        elif i % primary_modulo == 0 and i % secondary_modulo == 0:
            velocities.append(overlap_value)
        elif i % primary_modulo == 0:
            velocities.append(primary_value)
        elif i % secondary_modulo == 0:
            velocities.append(secondary_value)
        else:
            velocities.append(normal_value)
    return velocities

sieve_objs = create_sieve_objs(sieve_dict)
largest_period = find_largest_period(sieve_dict)

for n, s in sieve_objs:
    s.setZRange(0, largest_period - 1)
    binary = s.segment(segmentFormat='binary')
    indices = numpy.nonzero(binary)[0]

    for i in indices:
        filename = f'{title}_{n}_shift_clip{i + 1}.mid'
        shifted_sieve = shift_sieve(s, i)
        velocities = accent_velocity(shifted_sieve, primary_modulo=8, secondary_modulo=5)
        create_midi(shifted_sieve, largest_period, filename, velocities)

    original_sieve = prime_sieve(s)
    filename = f'{title}_{n}_prime.mid'
    velocities = accent_velocity(original_sieve, primary_modulo=8, secondary_modulo=5)
    create_midi(original_sieve, largest_period, filename, velocities)

    inverted_sieve = invert_sieve(s)
    filename = f'{title}_{n}_invert.mid'
    velocities = accent_velocity(inverted_sieve, primary_modulo=8, secondary_modulo=5)
    create_midi(inverted_sieve, largest_period, filename, velocities)

    reversed_sieve = reverse_sieve(s)
    filename = f'{title}_{n}_reverse.mid'
    velocities = accent_velocity(reversed_sieve, primary_modulo=8, secondary_modulo=5)
    create_midi(reversed_sieve, largest_period, filename, velocities)

    f = 2
    stretched_sieve = stretch_sieve(s, f)
    filename = f'{title}_{n}_stretch_{f}.mid'
    velocities = accent_velocity(stretched_sieve, primary_modulo=8, secondary_modulo=5)
    create_midi(stretched_sieve, largest_period, filename, velocities)