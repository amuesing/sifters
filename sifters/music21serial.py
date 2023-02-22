import music21

# aRow = music21.serial.getHistoricalRowByName('RowBergViolinConcerto')
# aRow.show('text')
# aMatrix = aRow.matrix()
# print(aMatrix)

# bStream = music21.stream.Stream()
# for i in range(0, 12, 3):
#     c = music21.chord.Chord(aRow[i:i + 3])
#     c.addLyric(c.primeFormString)
#     c.addLyric(c.forteClass)
#     bStream.append(c)
# bStream.show()

r = music21.serial.TwelveToneRow([1, 8, 4, 11, 7, 9])
m = r.matrix()

# print([str(e.pitchClass) for e in m[0]])

# print(m[0].pitches)

# print([e for e in s])


# print([str(e.pitch) for e in m[0]])
print(m)