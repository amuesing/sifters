from music21 import *
from itertools import *
from modules import *
import pandas as pd

def main():
    p_s = utilities.load_pickle('sifters/data/p_s.p')
    c = generate_score(p_s)
    # c.write('midi', 'sifters/data/score.mid')
    # c.show('text')
    df = utilities.generate_df(c)
    remove_dups = df.drop_duplicates()
    sorted_part = remove_dups.sort_values(by = 'Offset')
    test.csv_to_midi(sorted_part)
    sorted_part.to_csv("sifters/data/exported_data.csv", index=False)
    # # c.show('midi')
    # c.show()
    # print(c)
    # p.show()

# introduce metric-modulation through tempo changes -- augment/diminiute duration values relative to each part 
def generate_score(siev):
    score = stream.Score()
    score.insert(0, metadata.Metadata())
    score.insert(0, tempo.MetronomeMark('mid', 69, note.Note(type='quarter')))
    score.metadata.title = 'Sifters'
    score.metadata.composer = 'Aarib Moosey'
    binary = initialize.binary(siev)
    intervals = initialize.intervals(siev)[0]
    period = len(binary[0])
    factors = utilities.factorize(period)
    factors.reverse()
    #number of voices equals number of factors since what is being represented is each factoral of the period
    voices = len(factors)
    num, den = utilities.largest_prime_factor(len(binary[0])), 4
    parts = []
    part_number = 1
    for _ in range(voices):
        part = stream.Stream()
        p = stream.Stream()
        part.append(instrument.UnpitchedPercussion())
        part.insert(0, clef.PercussionClef())
        part.append(instrument.Piano())
        for bin in binary:
            p.insert(0, generate_percussion_part(bin, factors[part_number - 1]))
        for i in p:
            parts.insert(0, i)
        part_number += 1
    # flatten the streams, render as text, remove duplicate elements, recombine into a single midi layer
    for part in parts:
        part.insert(0, instrument.UnpitchedPercussion())
        part.insert(0, clef.PercussionClef())
        part.insert(0, meter.TimeSignature('{n}/{d}'.format(n=num, d=den)))
        score.insert(0, part)
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