import numpy as np
import re

from music21 import *

def periodicity(siev):
    numbers = [int(s) for s in re.findall(r'(\d+)@', siev)]
    unique_numbers = list(set(numbers))
    # prime_factors = 
    product = np.prod(unique_numbers)
    return product - 1

def generate_midi(events):
    s = stream.Stream()
    # time = 1
    for event in events:
        if event == 0:
            s.append(note.Rest())
        else:
            s.append(note.Note("C4"))
    s.show('midi')
    # s.write('midi', 'tests/generated.midi')

psappha_sieve = '(((8@0|8@1|8@7)&(5@1|5@3))|((8@0|8@1|8@2)&5@0)|((8@5|8@6)&(5@2|5@3|5@4))|8@3|8@4|(8@1&5@2)|(8@6&5@1))'
siev = '((3@1&2@1)|(4@2))'
a = sieve.Sieve(psappha_sieve)
a.setZRange(0, periodicity(psappha_sieve))
events = a.segment(segmentFormat='binary')
generate_midi(events)

# print(events)

# https://stackoverflow.com/questions/4289331/how-to-extract-numbers-from-a-string-in-python
# https://web.mit.edu/music21/doc/moduleReference/moduleSieve.html#music21.sieve.Sieve