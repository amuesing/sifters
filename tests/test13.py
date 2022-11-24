from music21 import *
from music21.stream.makeNotation import consolidateCompletedTuplets

s = stream.Stream()
r = note.Rest(quarterLength=1/6)
s.repeatAppend(r, 5)
s.insert(5/6, note.Note(duration=r.duration))
# consolidateCompletedTuplets(s)
# print([el.quarterLength for el in s.notesAndRests])
# s.show()

s2 = stream.Stream()
n = note.Note(quarterLength=1/3)
s2.repeatAppend(n, 3)
consolidateCompletedTuplets(s)
# print([el.quarterLength for el in s2.notesAndRests])
# s2.show()

# a = stream.Stream()
# a.insert(20, note.Note('C4'))
# a.insert(30, note.Note('D4'))
# # a.show('text')

# b = a.makeRests(fillGaps=True, inPlace=False, hideRests=True)
# b.show('text')

a = stream.Part()
a.insert(4, note.Note('C4'))
a.insert(8, note.Note('D4'))
a.insert(0, meter.TimeSignature('4/4'))
a.makeMeasures(inPlace=True)
a.makeRests(fillGaps=True, inPlace=True)
# a.show('text', addEndTimes=True)
a.show()

