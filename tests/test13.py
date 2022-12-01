from music21 import *
from music21.stream.makeNotation import consolidateCompletedTuplets

sBach = corpus.parse('bach/bwv7.7')
for p in sBach.parts:
    print("Part: ", p.id)
    for n in p.flat.notes:
        print(n.pitch.midi)