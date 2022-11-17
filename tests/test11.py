from music21 import *

strm = stream.Stream()
strm.append(tempo.MetronomeMark(number=20))

tempo_test = stream.Score()

tempo_test_part1 = stream.Part()
tempo_test_part2 = stream.Part()

# tempo_test_part1.append(tempo.MetronomeMark(number=20))
n = note.Note(midi=55)
n.notehead = 'diamond'
tempo_test_part1.append(n)
tempo_test_part1.append(note.Note('F4', type='quarter'))
tempo_test_part1.append(note.Note('B4', type='quarter'))
tempo_test_part1.append(note.Note('C4', type='quarter'))

# tempo_test_part2.append(tempo.MetronomeMark(number=20))
tempo_test_part2.append(note.Note('C4', type='quarter'))
tempo_test_part2.append(note.Note('F4', type='quarter'))
tempo_test_part2.append(note.Note('B4', type='quarter'))
tempo_test_part2.append(note.Note('C4', type='quarter'))


# tempo_test.insert(0, tempo.MetronomeMark(number=20))
tempo_test.insert(0, tempo_test_part1)
tempo_test.insert(0, tempo_test_part2)

# strm.append(tempo_test)
# strm.show()

part1 = tempo_test.parts[0]
part1.insert(0, tempo.MetronomeMark('fast', 144, note.Note(type='half')))
part1.staffLines = 1

part1.show()