import music21

aRow = music21.serial.getHistoricalRowByName('RowBergViolinConcerto')
aRow.show('text')
aMatrix = aRow.matrix()
print(aMatrix)

bStream = music21.stream.Stream()
for i in range(0, 12, 3):
    c = music21.chord.Chord(aRow[i:i + 3])
    c.addLyric(c.primeFormString)
    c.addLyric(c.forteClass)
    bStream.append(c)
bStream.show()