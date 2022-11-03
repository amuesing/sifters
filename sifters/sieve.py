import numpy as np
import re

from music21 import *

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

def write_part(siev):
    part = stream.Part()
    period = len(siev)
    part.append(instrument.UnpitchedPercussion())
    part.append(meter.TimeSignature('{n}/8'.format(n=period)))
    part.append(tempo.MetronomeMark('fast', 144, note.Note(type='quarter')))
    for point in siev:
        if point == 0:
            part.append(note.Note(midi=76, type='eighth'))
        else:
            part.append(note.Note(midi=77, type='eighth'))
    return part.write('midi', 'data/generated.midi')

#stream of streams
def generate_stream(sievs):
    s = stream.Stream()
    for siev in sievs:
        s.append(write_part(siev))
    return s
    
def play(midi):
    s = converter.parse(midi)
    s.show('midi')

psappha_sieve = '(((8@0|8@1|8@7)&(5@1|5@3))|((8@0|8@1|8@2)&5@0)|((8@5|8@6)&(5@2|5@3|5@4))|8@3|8@4|(8@1&5@2)|(8@6&5@1))'
siev = initialize(psappha_sieve)
play(write_part(siev))