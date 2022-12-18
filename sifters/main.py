from music21 import *
from modules import *

def main():
    p_s = utilities.load_pickle('sifters/data/p_s.p')
    c = generate_score(p_s)
    c.show()

def generate_score(siev):
    score = stream.Score()
    score.insert(0, metadata.Metadata())
    score.metadata.title = 'Sifters'
    score.metadata.composer = 'Aarib Moosey'
    binary = initialize.binary(siev)
    period = len(binary[0])
    intervals = initialize.pitch_set(siev)
    factors = utilities.factorize(period)
    num, den = utilities.largest_prime_factor(len(binary[0])), 2
    index = -1
    voices = len(binary)
    parts = stream.Stream()
    for _ in range(voices):
        part = stream.Stream()
        p = stream.Stream()
        for bin in binary:
            p.insert(0, generate_part(bin, intervals, factors[index]))
        for i in p:
            for n in i:
                part.insert(n.offset, n)
        parts.insert(0, part)
        index += -1
    for part in parts:
        part.insert(0, meter.TimeSignature('{n}/{d}'.format(n=num, d=den)))
        score.insert(0, part)
    return score

def generate_part(bin, intervals, id):
    part = stream.Part()
    period = len(bin)
    pattern = bin * id
    duration = 0.25 * (period/id)
    # smallest duration set to 0.25, or one 16th note
    inter = intervals * 100
    # what if there are more events than intervals, how to cycle?
    index = id - 1
    i = 0
    for bit in pattern:
        if bit == 1:
            part.insert(i * duration, note.Note(midi=60+(inter[index]), quarterLength=duration))
            index += 1
        i += 1
    return part

if __name__ == '__main__':
    main()