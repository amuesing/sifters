import numpy as np
import re

from music21 import *

def periodicity(siev):
    numbers = [int(s) for s in re.findall(r'(\d+)@', siev)]
    unique_numbers = list(set(numbers))
    # prime_factors = 
    product = np.prod(unique_numbers)
    return product - 1 

siev = '8@0&5@0'

a = sieve.Sieve(siev)
a.setZRange(0, periodicity(siev))

print(a.segment(segmentFormat='binary'))

# https://stackoverflow.com/questions/4289331/how-to-extract-numbers-from-a-string-in-python
# https://web.mit.edu/music21/doc/moduleReference/moduleSieve.html#music21.sieve.Sieve