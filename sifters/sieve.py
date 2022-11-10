import numpy as np
import re

from music21 import *

def save(s):
    return s.write('midi', 'data/track/generate.midi')

def play(midi):
    s = converter.parse(midi)
    s.show('midi')

def find_period(siev):
    numbers = [int(s) for s in re.findall(r'(\d+)@', siev)]
    unique_numbers = list(set(numbers))
    product = np.prod(unique_numbers)
    return product - 1

def initialize(siev):
    a = sieve.Sieve(siev)
    a.setZRange(0, find_period(siev))
    events = a.segment(segmentFormat='binary')
    return events

def intersect(sievs):
    s = '|'.join(sievs)
    return s
    

def parse(sievs):
    s = []
    for siev in sievs:
        s.append(initialize(siev))
    return s

#input: siev
#output: sievs
def train(siev):
    pattern = initialize(siev)
    #write an extraction function which splits the siev object by where ')|(' occurs
    numbers = re.findall(r'\)\|', siev)
    # numbers = [int(s) for s in re.findall(r'\)\|', siev)] 
    # n = note.Note()
    # s = siev
    print(numbers)

#input: sievs
#output: pattern, midi_key, note_length
def assign(sievs):
    print('hello world')

def generate_part(pattern):
    midi_key=76
    note_length=0.5
    part = stream.Part()
    period = len(pattern)
    part.append(instrument.UnpitchedPercussion())
    part.append(meter.TimeSignature('{n}/8'.format(n=period)))
    # make pattern
    for point in pattern:
        if point == 0:
            part.append(note.Note(midi=midi_key, quarterLength=note_length))
        else:
            part.append(note.Note(midi=midi_key+1, quarterLength=note_length))
    return part
    
# def parse(sievs):
#     s = stream.Stream()
#     midi_key = [76, 47, 67]
#     i = 0
#     for siev in sievs:
#         siev = initialize(siev)
#         s.append(generate_part(siev, midi_key[i]))
#         i += 1
#     return s

def generate_stream(siev):
    s = stream.Stream()
    s.append(tempo.MetronomeMark('fast', 144, note.Note(type='quarter')))
    if len(siev) > 1:
        sievs = parse(siev)
        for siv in sievs:
            s.append(generate_part(siv))
    return s

# psappha_sieve = '((8@0|8@1|8@7)&(5@1|5@3))|((8@0|8@1|8@2)&5@0)|((8@5|8@6)&(5@2|5@3|5@4))|(8@3)|(8@4)|(8@1&5@2)|(8@6&5@1)'
# when all have same period
sievs = '((8@0|8@1|8@7)&(5@1|5@3))', '((8@0|8@1|8@2)&5@0)', '((8@5|8@6)&(5@2|5@3|5@4))', '(8@6&5@1)' #'(8@3)', '(8@4)', '(8@1&5@2)', 

# parsed_sievs = parse(sievs)

# instrument key (instrumentation)
s = generate_stream(sievs)
s.show()
