from music21 import *

strm = stream.Stream()
strm.append(tempo.MetronomeMark(number=20))

tempo_test = stream.Score()

tempo_test_part1 = stream.Part()
tempo_test_part2 = stream.Part()

tempo_test_part1.append(tempo.MetronomeMark(number=20))
tempo_test_part1.append(note.Note('C4', type='quarter'))
tempo_test_part1.append(note.Note('F4', type='quarter'))
tempo_test_part1.append(note.Note('B4', type='quarter'))

# tempo_test_part2.append(tempo.MetronomeMark(number=20))
tempo_test_part2.append(note.Note('C4', type='quarter'))
tempo_test_part2.append(note.Note('F4', type='quarter'))
tempo_test_part2.append(note.Note('B4', type='quarter'))


# tempo_test.insert(0, tempo.MetronomeMark(number=20))
tempo_test.insert(0, tempo_test_part1)
tempo_test.insert(0, tempo_test_part2)

strm.append(tempo_test)
# strm.show()


tempo_test.show()