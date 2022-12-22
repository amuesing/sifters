from music21 import metadata, stream, note, instrument, clef, meter
from itertools import cycle
from modules import *

def main():
    p_s = utilities.load_pickle('sifters/data/p_s.p')
    c = generate_score(p_s)
    # c.show()

def generate_score(siev):
    score = stream.Score()
    score.insert(0, metadata.Metadata())
    score.metadata.title = 'Sifters'
    score.metadata.composer = 'Aarib Moosey'
    binary = initialize.binary(siev)
    period = len(binary[0])
    intervals = initialize.pitch_set(siev)
    factors = utilities.factorize(period)
    factors.reverse()
    num, den = utilities.largest_prime_factor(len(binary[0])), 2
    part_number = 1
    voices = len(binary)
    parts = stream.Stream()
    for _ in range(voices):
        part = stream.Stream()
        p = stream.Stream()
        if part_number == 1:
            part.append(instrument.UnpitchedPercussion())
            part.insert(0, clef.PercussionClef())
        if part_number > 1:
            part.append(instrument.Piano())
        for bin in binary:
            p.insert(0, generate_part(bin, intervals, factors[part_number - 1], part_number))
        for i in p:
            for n in i:
                part.insert(n.offset, n)
        parts.insert(0, part)
        part_number += 1
    for part in parts:
        part.insert(0, meter.TimeSignature('{n}/{d}'.format(n=num, d=den)))
        score.insert(0, part)
    return score

def generate_part(bin, intervals, factor, part_number):
    part = stream.Part()
    period = len(bin)
    pattern = bin * factor
    duration = 0.25 * (period/factor)
    midi_key = cycle([44, 60, 76, 80, 80, 80, 35, 35])
    inter = cycle(intervals)
    fund= 60
    i = 0
    if part_number == 1:
        for bit in pattern:
            if bit == 1:
                part.insert(i * duration, note.Note(midi=next(midi_key), quarterLength=duration))
            i += 1
    for bit in pattern:
        if bit == 1:
            part.insert(i * duration, note.Note(midi=fund + (next(inter)), quarterLength=duration))
        i += 1
    return part

if __name__ == '__main__':
    main()