from music21 import *
from itertools import *
from modules import *

def main():
    p_s = utilities.load_pickle('sifters/data/p_s.p')
    score = generate_score(p_s)
    dataframe = formalize.generate_df(score)
    sorted = utilities.sort_values(dataframe, 'Offset')
    sorted.to_csv("sifters/data/exported_data.csv", index=False)
    combined_part = formalize.csv_to_midi(dataframe)
    composition = formalize.measure_zero(combined_part)
    composition.write('midi', 'sifters/data/percussion.mid')

# introduce metric-modulation through tempo changes -- augment/diminiute duration values relative to each part 
def generate_score(siev):
    score = stream.Score()
    binary = initialize.binary(siev)
    period = len(binary[0])
    factors = utilities.factorize(period)
    factors.reverse()
    voices = len(factors)
    parts = []
    part_number = 1
    for _ in range(voices):
        part = stream.Stream()
        p = stream.Stream()
        for bin in binary:
            p.insert(0, generate_percussion_part(bin, factors[part_number - 1]))
        for i in p:
            parts.insert(0, i)
        part_number += 1
    for part in parts:
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