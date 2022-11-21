import numpy as np
import re

from music21 import *

def save(stream):
    return stream.write('midi', 'data/track/generated.midi')

def play(midi_file):
    stream = converter.parse(midi_file)
    stream.show('midi')

def find_period(siev):
    numbers = [int(s) for s in re.findall(r'(\d+)@', siev)]
    unique_numbers = list(set(numbers))
    product = np.prod(unique_numbers)
    return product

def intersect(sievs):
    intersection = '|'.join(sievs)
    return intersection

###################################################

def parse_modulo(siev):
    if type(siev) == tuple:
        modulo = []
        for siv in siev:
            modulo.append([int(s) for s in re.findall(r'(\d+)@', siv)])
        return modulo
    else:
        modulo = [int(s) for s in re.findall(r'(\d+)@', siev)]
        return modulo

def find_lcm(modulo):
    if type(modulo[0]) == list:
        multiples = []
        for mod in modulo:
            multiples.append(np.lcm.reduce(mod))
        return multiples
    else:
        return np.lcm.reduce(modulo)
    
def find_repeats(period, lcm):
    repeats = []
    for m in lcm:
        repeats.append(int(period/m))
    return repeats

def merge(list1, list2):
    merged_list = [(list1[i], list2[i]) for i in range(0, len(list1))]
    return merged_list
# https://www.geeksforgeeks.org/python-merge-two-lists-into-list-of-tuples/

def normalize_periodicity(sievs):
    mod = parse_modulo(sievs)
    lcm = find_lcm(mod)
    period = find_lcm(lcm)
    repeats = find_repeats(period, lcm)
    # multi = merge(sivs, repeats)
    # return multi
    return repeats

###################################################

def initialize(siev, rep):
    events = sieve.Sieve(siev)
    events.setZRange(0, (rep * find_period(siev)) - 1)
    binary = events.segment(segmentFormat='binary')
    return binary

def assign(pattern, index):
    # method for selecting midi key
    midi_key = [35, 60, 76, 80, 80, 80 ,80]
    note_length = 0.5
    return [pattern, midi_key[index], note_length]

def parse(sievs):
    pattern = []
    i = 0
    rep = normalize_periodicity(sievs)
    for siev in sievs:
        binary = initialize(siev, rep[i])
        assigned_pattern = assign(binary, i)
        pattern.append(assigned_pattern)
        i += 1
    return pattern

###################################################

def generate_measure(segment, midi_key, note_length, measure_num):
    measure = stream.Measure(number=measure_num)
    for point in segment:
        if point == 0:
            measure.append(note.Rest(quarterLength=note_length))
        else:
            measure.append(note.Note(midi=midi_key, quarterLength=note_length))
    return measure

def generate_part(pattern, midi_key, note_length, id):
    part = stream.Part(id='part{n}'.format(n=id))
    part.append(instrument.UnpitchedPercussion())
    part.append(clef.PercussionClef())
    measure_num = 1
    repeat_pattern = 10
    period = 5
    # method for finding time signature neumerator/denominator
    part.append(meter.TimeSignature('{n}/8'.format(n=period)))
    split_pattern = np.array_split(pattern, 8)
    for _ in range(repeat_pattern):
        for segment in split_pattern:
            part.append(generate_measure(segment, midi_key, note_length, measure_num))
            measure_num += 1
    return part

def generate_score(siev):
    s = stream.Score()
    id = 1
    if len(siev) > 1:
        sievs = parse(siev)
        for siv in sievs:
            pattern, midi_key, note_length = siv[0], siv[1], siv[2]
            s.insert(0, generate_part(pattern, midi_key, note_length, id))
            id += 1
    else:
        print('hello world')
    s.insert(0, metadata.Metadata())
    s.metadata.title = 'Sifters'
    s.metadata.composer = 'Aarib Moosey'
    p1m1 = s.parts[0].measure(1)
    p1m1.insert(0, tempo.MetronomeMark('fast', 144, note.Note(type='half')))
    return s

if __name__ == '__main__':
    # norm = normalize_periodicity(sivs))
    print(normalize_periodicity(sivs))