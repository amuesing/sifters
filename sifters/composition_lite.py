import mido
import music21
import numpy

title = 'starbird'

# Rhythmic patterns dictionary
patterns = {
    'snare': '(8@0|8@1|8@7)&(5@1|5@3)|((8@0|8@1|8@2)&5@0)|((8@5|8@6)&(5@2|5@3|5@4))',
    'tom': '(((8@0|8@1|8@7)&(5@1|5@3))|((8@0|8@1|8@2)&5@0)|((8@5|8@6)&(5@2|5@3|5@4))|(8@6&5@1)|(8@3)|(8@4)|(8@1&5@2))',
    'kick': '(8@3)|(8@4)',
    'woodblock': '(8@1&5@2)',
    'impact': '(8@6&5@1)'
}

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

def create_midi(binary, period, filename):
    # Create a MIDI file
    mid = mido.MidiFile()

    # Create a MIDI track
    track = mido.MidiTrack()
    mid.tracks.append(track)
    
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


# Process each rhythmic pattern in the dictionary
for name, sieve in patterns.items():
    # Create a Sieve object
    s = music21.sieve.Sieve(sieve)
    
    # Calculate the period
    period = s.period()
    
    # Set Z-range
    s.setZRange(0, period - 1)
    
    # Get the binary segment
    binary = s.segment(segmentFormat='binary')
    indices = numpy.nonzero(binary)[0]

    ticks_per_quarter_note = 480
    # Duration should match with denominator
    duration = ticks_per_quarter_note // 4
    
    # Apply transformations and create MIDI files
    for i in indices:
        filename = f'{title}_{name}_shift_{i}.mid'
        shifted_sieve = shift_sieve(s, i)
        create_midi(shifted_sieve, period, filename)
    
    inverted_sieve = invert_sieve(s)
    filename = f'{title}_{name}_invert.mid'
    create_midi(inverted_sieve, period, filename)
    
    reversed_sieve = reverse_sieve(s)
    filename = f'{title}_{name}_reverse.mid'
    create_midi(reversed_sieve, period, filename)
    
    # Example of stretching with a factor of 2
    f = 2
    stretched_sieve = stretch_sieve(s, f)
    filename = f'{title}_{name}_stretch_{f}.mid'
    create_midi(stretched_sieve, period, filename)
