from music21 import *

aStream = stream.Stream()
src = list(range(12)) # cheate a list of integers 0 through 11
# src = src[2:4] + src[0:2] + src[8:9] + src[4:8] + src[9:12] # recombine
for i in range(0, 12, 3):
    # aStream.append(chord.Chord(src[i:i + 3]))
    print(src[i:i+3])

# aStream.show()
# print(src[4:8])
# print(range(0, 12, 3))
# print(src)

# print(src[i:i+3])