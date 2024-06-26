import mido
import music21
import numpy as np

title = 'starbird'

# Rhythmic patterns dictionary
sieve_dict = {
    'snare': '(8@0|8@1|8@7)&(5@1|5@3)|((8@0|8@1|8@2)&5@0)|((8@5|8@6)&(5@2|5@3|5@4))',
    'clap': '(((8@0|8@1|8@7)&(5@1|5@3))|((8@0|8@1|8@2)&5@0)|((8@5|8@6)&(5@2|5@3|5@4))|(8@6&5@1)|(8@3)|(8@4)|(8@1&5@2))',
    'kick': '(8@3)|(8@4)',
    'woodblock': '(8@1&5@2)',
    'impact': '(8@6&5@1)'
}

def prime_sieve(sieve):
    binary = np.array(sieve.segment(segmentFormat='binary'))
    return binary

# Shift transformation
def shift_sieve(sieve, shift_amount):
    binary = np.array(sieve.segment(segmentFormat='binary'))  # Convert to NumPy array
    shifted_binary = np.roll(binary, shift_amount)
    return shifted_binary

# Inversion transformation
def invert_sieve(sieve):
    binary = np.array(sieve.segment(segmentFormat='binary'))  # Convert to NumPy array
    inverted_binary = 1 - binary
    return inverted_binary

# Reverse transformation
def reverse_sieve(sieve):
    binary = np.array(sieve.segment(segmentFormat='binary'))  # Convert to NumPy array
    reversed_binary = binary[::-1]
    return reversed_binary

# Stretching (Scaling) transformation
def stretch_sieve(sieve, factor):
    binary = np.array(sieve.segment(segmentFormat='binary'))  # Convert to NumPy array
    stretched_binary = np.repeat(binary, factor)
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

def get_velocity(instrument, position, period):
    # Enhanced velocity assignment logic
    if instrument == 'snare':
        velocity = 100 if position % period in [0, 2, 4, 6] else 60
    elif instrument == 'clap':
        velocity = 60 + (position % period) * 10  # varies within a range
    elif instrument == 'kick':
        velocity = 120
    elif instrument in ['woodblock', 'impact']:
        velocity = 90
    else:
        velocity = 80  # default velocity for other instruments

    # Clamp velocity to be within the valid MIDI range
    return max(0, min(127, velocity))

def create_midi(binary, period, filename, instrument):
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)

    ticks_per_quarter_note = 480
    duration = ticks_per_quarter_note // 4

    for position, value in enumerate(binary):
        velocity = get_velocity(instrument, position, period)
        if value == 0:
            track.append(mido.Message('note_off', note=64, velocity=0, time=duration))
        else:
            track.append(mido.Message('note_on', note=64, velocity=velocity, time=0))
            track.append(mido.Message('note_off', note=64, velocity=0, time=duration))

    numerator = period
    denominator = 16
    time_signature = mido.MetaMessage('time_signature', numerator=numerator, denominator=denominator, time=0)
    track.append(time_signature)
    track.append(mido.MetaMessage('track_name', name=filename, time=0))
    
    mid.save(f'data/mid/{filename}')

if __name__ == "__main__":
    sieve_objs = create_sieve_objs(sieve_dict)
    largest_period = find_largest_period(sieve_dict)

    for n, s in sieve_objs:
        s.setZRange(0, largest_period - 1)
        binary = s.segment(segmentFormat='binary')
        indices = np.nonzero(binary)[0]

        for i in indices:
            filename = f'{title}_{n}_shift_clip{i + 1}.mid'
            shifted_sieve = shift_sieve(s, i)
            create_midi(shifted_sieve, largest_period, filename, n)

        original_sieve = prime_sieve(s)
        filename = f'{title}_{n}_prime.mid'
        create_midi(original_sieve, largest_period, filename, n)

        inverted_sieve = invert_sieve(s)
        filename = f'{title}_{n}_invert.mid'
        create_midi(inverted_sieve, largest_period, filename, n)

        reversed_sieve = reverse_sieve(s)
        filename = f'{title}_{n}_reverse.mid'
        create_midi(reversed_sieve, largest_period, filename, n)

        f = 2
        stretched_sieve = stretch_sieve(s, f)
        filename = f'{title}_{n}_stretch_{f}.mid'
        create_midi(stretched_sieve, largest_period, filename, n)