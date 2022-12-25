from music21 import *
from itertools import *
from modules import *

def main():
    p_s = utilities.load_pickle('sifters/data/p_s.p')
    c = generate_score(p_s)
    c.write('midi', 'sifters/data/generated.mid')
    # c.write
    # c.show()
    # print(c)

# introduce metric-modulation through tempo changes -- augment/diminiute duration values relative to each part 
def generate_score(siev):
    score = stream.Stream()
    percussion = stream.Stream()
    parts = []
    score.insert(0, metadata.Metadata())
    score.insert(0, tempo.MetronomeMark('mid', 69, note.Note(type='quarter')))
    score.metadata.title = 'Sifters'
    score.metadata.composer = 'Aarib Moosey'
    binary = initialize.binary(siev)
    intervals = initialize.intervals(siev)[0]
    period = len(binary[0])
    factors = utilities.factorize(period)
    factors.reverse()
    voices = len(factors)
    num, den = utilities.largest_prime_factor(len(binary[0])), 4
    part_number = 1
    for _ in range(voices):
        part = stream.Part()
        p = stream.Part()
        for bin in binary:
            p.insert(0, generate_percussion_part(bin, factors[part_number - 1]))
        for i in p:
            for n in i:
                part.insert(n.offset, n)
        parts.append(part)
        part_number += 1
    # how do I merge all midi layers into a single layer?
    # if finale is only able to display 4 layers per stave, then any iteration in excess of 4 will be left out
    # flatten the streams, render as text, remove duplicate elements, recombine into a single midi layer
    for part in parts:
        part.insert(0, instrument.UnpitchedPercussion())
        part.insert(0, clef.PercussionClef())
        part.insert(0, meter.TimeSignature('{n}/{d}'.format(n=num, d=den)))
        score.insert(0, part)
    # for part in parts:
        # for n in part:
        #     percussion.insert(n.offset, n)
    return score

def generate_percussion_part(bin, factor):
    part = stream.Part()
    period = len(bin)
    repeat = 1
    unit = 0.25
    pattern = (bin * factor) * repeat
    duration = unit * (period/factor)
    events = formalize.midi_pool(bin)
    midi_pool = cycle(events)
    i = 0
    for bit in pattern:
        if bit == 1:
            part.insert(i * duration, note.Note(midi=next(midi_pool), quarterLength=unit))
        i += 1
    return part

# def generate_part(bin, intervals, factor, part_number):
#     part = stream.Part()
#     period = len(bin)
#     repeat = 1
#     pattern = (bin * factor) * repeat
#     duration = 0.25 * (period/factor)
#     midi_key = cycle([44, 60, 76, 80, 80, 80, 35, 35])
#     inter = cycle(intervals)
#     fund= 60
#     i = 0
#     # if part_number == 1:
#     for bit in pattern:
#         if bit == 1:
#             part.insert(i * duration, note.Note(midi=next(midi_key), quarterLength=duration))
#         i += 1
#     # else:
#     #     for bit in pattern:
#     #         if bit == 1:
#     #             part.insert(i * duration, note.Note(midi=60 + (next(inter)), quarterLength=duration))
#     #         i += 1
#     return part

if __name__ == '__main__':
    main()