from music21 import *
import math

psa = sieve.PitchSieve('((8@0|8@1|8@7)&(5@1|5@3))|((8@0|8@1|8@2)&5@0)|((8@5|8@6)&(5@2|5@3|5@4))|(8@3)|(8@4)|(8@1&5@2)|(8@6&5@1)')
s = stream.Stream()
period = psa.sieveObject.period()
psa.sieveObject.setZRange(0, period - 1)
intervals = psa.sieveObject.segment()
mid = []


f = 36

def largest_prime_factor(n):
    return next(n // i for i in range(1, n) if n % i == 0 and is_prime(n // i))

def is_prime(m):
    return all(m % i for i in range(2, m - 1))

for i in intervals:
    # s.append(note.Note(f+i))
    mid.append(f+i)

largest_prime = largest_prime_factor(period)

a = mid[::2]
b = mid[1::2]

for i in range(0, len(intervals), 3):
    s.append(chord.Chord(a[i:i+3]))
    # print(chord.Chord(mid[i:i+largest_prime]))

# s.show()

# print(mid[::2])
# print(mid1)
# print(mid2)

crisscross = [item for sublist in zip(a,b) for item in sublist]

print(crisscross)