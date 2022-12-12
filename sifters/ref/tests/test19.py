from music21 import *

a = stream.Stream()
a.append([note.Note('B2'), note.Note('G3')])
b = stream.Stream()
b.append([note.Note('D3'), note.Note('B4')])

for n in b.notes:
    a.insert(n.offset, n)
    # print(n)

a.show()
# print(b.notes)