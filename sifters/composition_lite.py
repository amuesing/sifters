import mido
import music21
import numpy

title = 'starbird'

# Rhythmic patterns dictionary
sieve_dict = {
    'snare': '(8@0|8@1|8@7)&(5@1|5@3)|((8@0|8@1|8@2)&5@0)|((8@5|8@6)&(5@2|5@3|5@4))',
    'tom': '(((8@0|8@1|8@7)&(5@1|5@3))|((8@0|8@1|8@2)&5@0)|((8@5|8@6)&(5@2|5@3|5@4))|(8@6&5@1)|(8@3)|(8@4)|(8@1&5@2))',
    'kick': '(8@3)|(8@4)',
    'woodblock': '(8@1&5@2)',
    'impact': '(8@6&5@1)'
}

def prime_sieve(sieve):
    binary = numpy.array(sieve.segment(segmentFormat='binary'))
    return binary

# Shift transformation
def shift_sieve(sieve, shift_amount):
    binary = numpy.array(sieve.segment(segmentFormat='binary'))  # Convert to NumPy array
    shifted_binary = numpy.roll(binary, shift_amount)
    return shifted_binary

# Inversion transformation
def invert_sieve(sieve):
    binary = numpy.array(sieve.segment(segmentFormat='binary'))  # Convert to NumPy array
    inverted_binary = 1 - binary
    return inverted_binary

# Reverse transformation
def reverse_sieve(sieve):
    binary = numpy.array(sieve.segment(segmentFormat='binary'))  # Convert to NumPy array
    reversed_binary = binary[::-1]
    return reversed_binary

# Stretching (Scaling) transformation
def stretch_sieve(sieve, factor):
    binary = numpy.array(sieve.segment(segmentFormat='binary'))  # Convert to NumPy array
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

def create_midi(binary, period, filename):
    # Create a MIDI file
    mid = mido.MidiFile()

    # Create a MIDI track
    track = mido.MidiTrack()
    mid.tracks.append(track)

    ticks_per_quarter_note = 480
    # Duration should match with denominator
    duration = ticks_per_quarter_note // 4
    
    # Add note events
    for value in binary:
        if value == 0:
            track.append(mido.Message('note_on', note=64, velocity=0, time=0))
            track.append(mido.Message('note_off', note=64, velocity=0, time=duration))
        else:
            track.append(mido.Message('note_on', note=64, velocity=100, time=0))
            track.append(mido.Message('note_off', note=64, velocity=100, time=duration))

    # Create a time signature message
    numerator = period
    denominator = 16  # You can adjust this as needed
    time_signature = mido.MetaMessage('time_signature', numerator=numerator, denominator=denominator, time=0)
    track.append(mido.MetaMessage('track_name'))

    track.append(time_signature)
    # Save the MIDI file
    mid.save(f'data/mid/{filename}')

sieve_objs = create_sieve_objs(sieve_dict)
# print(sieve_objs)
largest_period = find_largest_period(sieve_dict)

for n, s in sieve_objs:
    s.setZRange(0, largest_period - 1)
    binary = s.segment(segmentFormat='binary')
    indices = numpy.nonzero(binary)[0]
    
    # Apply transformations and create MIDI files
    for i in indices:
        filename = f'{title}_{n}_shift_clip{i + 1}.mid'
        shifted_sieve = shift_sieve(s, i)
        create_midi(shifted_sieve, largest_period, filename)
    
    original_sieve = prime_sieve(s)
    filename = f'{title}_{n}_prime.mid'
    create_midi(original_sieve, largest_period, filename)

    inverted_sieve = invert_sieve(s)
    filename = f'{title}_{n}_invert.mid'
    create_midi(inverted_sieve, largest_period, filename)
    
    reversed_sieve = reverse_sieve(s)
    filename = f'{title}_{n}_reverse.mid'
    create_midi(reversed_sieve, largest_period, filename)
    
    # Example of stretching with a factor of 2
    f = 2
    stretched_sieve = stretch_sieve(s, f)
    filename = f'{title}_{n}_stretch_{f}.mid'
    create_midi(stretched_sieve, largest_period, filename)
