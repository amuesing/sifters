import numpy as np
import re

from music21 import *

def save(stream):
    return stream.write('midi', 'data/track/generated.midi')

def play(midi_file):
    stream = converter.parse(midi_file)
    stream.show('midi')

def initialize(siev):
    events = sieve.Sieve(siev)
    events.setZRange(0, find_period(siev))
    pattern = events.segment(segmentFormat='binary')
    return pattern

def find_period(siev):
    numbers = [int(s) for s in re.findall(r'(\d+)@', siev)]
    unique_numbers = list(set(numbers))
    product = np.prod(unique_numbers)
    return product - 1

def parse(sievs):
    siv = []
    index = 0
    for siev in sievs:
        pattern = initialize(siev)
        assigned_pattern = assign(pattern, index)
        siv.append(assigned_pattern)
        index += 1
    return siv

def intersect(sievs):
    intersection = '|'.join(sievs)
    return intersection

def assign(pattern, index):
    midi_key = [35, 60, 76, 80]
    note_length = 0.5
    return [pattern, midi_key[index], note_length]


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
    repeat_pattern = 4
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

# psappha_sieve = '((8@0|8@1|8@7)&(5@1|5@3))|((8@0|8@1|8@2)&5@0)|((8@5|8@6)&(5@2|5@3|5@4))|(8@3)|(8@4)|(8@1&5@2)|(8@6&5@1)'
# when all have same period
# order sieves by LCM of modulo
# find LCM of all LCM
# find way to normalize all sieves so that they are equal lengths
sievs = '((8@0|8@1|8@7)&(5@1|5@3))', '((8@0|8@1|8@2)&5@0)', '((8@5|8@6)&(5@2|5@3|5@4))', '(8@6&5@1)' #'(8@3)', '(8@4)', '(8@1&5@2)', 

# instrument key (instrumentation)
s = generate_score(sievs)
# p = parse(sievs)
# print(p)
s.show()