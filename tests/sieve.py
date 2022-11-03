import numpy as np
import re

from music21 import *

def periodicity(siev):
    numbers = [int(s) for s in re.findall(r'(\d+)@', siev)]
    unique_numbers = list(set(numbers))
    product = np.prod(unique_numbers)
    return product - 1

def generate_midi(events):
    period = len(events)
    s = stream.Stream()
    p0 = stream.Part(id='part0')
    ts0 = meter.TimeSignature('{n}/8'.format(n=period))
    p0.append(instrument.UnpitchedPercussion())
    p0.append(ts0)
    p0.append(tempo.MetronomeMark('fast', 144, note.Note(type='quarter')))
    
    for event in events:
        if event == 0:
            p0.append(note.Note(midi=76, type='eighth'))
        else:
            p0.append(note.Note(midi=77, type='eighth'))
    

    s.append(p0)

    s.write('midi', 'tests/generated.midi')
    
def play(midi):
    s = converter.parse(midi)
    s.show('midi')

psappha_sieve = '(((8@0|8@1|8@7)&(5@1|5@3))|((8@0|8@1|8@2)&5@0)|((8@5|8@6)&(5@2|5@3|5@4))|8@3|8@4|(8@1&5@2)|(8@6&5@1))'
siev = '((3@1&2@1)|(4@2))'
# initialize a stream and append the sieve??
a = sieve.Sieve(psappha_sieve)
a.setZRange(0, periodicity(psappha_sieve))
events = a.segment(segmentFormat='binary')
generate_midi(events)


play('tests/generated.midi')

# print(events)

# https://stackoverflow.com/questions/4289331/how-to-extract-numbers-from-a-string-in-python
# https://web.mit.edu/music21/doc/moduleReference/moduleSieve.html#music21.sieve.Sieve