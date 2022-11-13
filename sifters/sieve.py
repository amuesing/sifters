import numpy as np
import re

from music21 import *

def save(stream):
    return stream.write('midi', 'data/track/generated.midi')

def play(midi):
    stream = converter.parse(midi)
    stream.show('midi')

def find_period(siev):
    numbers = [int(s) for s in re.findall(r'(\d+)@', siev)]
    unique_numbers = list(set(numbers))
    product = np.prod(unique_numbers)
    return product - 1

def intersect(sievs):
    intersection = '|'.join(sievs)
    return intersection

def initialize(siev):
    events = sieve.Sieve(siev)
    events.setZRange(0, find_period(siev))
    pattern = events.segment(segmentFormat='binary')
    return pattern

def assign(pattern, index):
    midi_key = [35, 60, 76, 80]
    note_length = 0.5
    return [pattern, midi_key[index], note_length]

def parse(sievs):
    siv = []
    index = 0
    for siev in sievs:
        pattern = initialize(siev)
        assigned_pattern = assign(pattern, index)
        siv.append(assigned_pattern)
        index += 1
    return siv

def generate_measure(pattern, midi_key, note_length, measure_num):
    measure = stream.Measure(number=measure_num)
    for point in pattern:
        if point == 0:
            measure.append(note.Rest(quarterLength=note_length))
        else:
            measure.append(note.Note(midi=midi_key, quarterLength=note_length))
    return measure

def generate_part(pattern, midi_key, note_length, id):
    part = stream.Part(id='part{n}'.format(n=id))
    part.append(instrument.UnpitchedPercussion())
    part.append(meter.TimeSignature('{n}/8'.format(n=len(pattern))))
    measure_num = 1
    repeats = 4
    for _ in range(repeats):
        part.append(generate_measure(pattern, midi_key, note_length, measure_num))
        measure_num += 1
    return part

def generate_stream(siev):
    s = stream.Score(id='mainScore')
    s.append(tempo.MetronomeMark('fast', 144, note.Note(type='half')))
    id = 0
    if len(siev) > 1:
        sievs = parse(siev)
        for siv in sievs:
            pattern = siv[0]
            midi_key = siv[1]
            note_length = siv[2]
            s.insert(0, generate_part(pattern, midi_key, note_length, id))
            id += 1
    return s

# psappha_sieve = '((8@0|8@1|8@7)&(5@1|5@3))|((8@0|8@1|8@2)&5@0)|((8@5|8@6)&(5@2|5@3|5@4))|(8@3)|(8@4)|(8@1&5@2)|(8@6&5@1)'
# when all have same period
sievs = '((8@0|8@1|8@7)&(5@1|5@3))', '((8@0|8@1|8@2)&5@0)', '((8@5|8@6)&(5@2|5@3|5@4))', '(8@6&5@1)' #'(8@3)', '(8@4)', '(8@1&5@2)', 

# instrument key (instrumentation)
s = generate_stream(sievs)
# p = parse(sievs)
# print(p)
s.show('midi')

