from music21 import *

sBach = corpus.parse('bach/bwv57.8')

alto = sBach.parts[1]

excerpt = alto.measure(1)

excerpt.insert(0, tempo.MetronomeMark('fast', 144, note.Note(type='half')))

excerpt.show()