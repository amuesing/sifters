import numpy as np

def serial(row):
    intervals = []
    columns = []
    for tone in row:
        interval = (tone - row[0])
        intervals.append(interval)
        columns.append([(row[0] + (row[0] - tone))] * len(row))
    return np.add(intervals, columns)

def fibonacci(fund, length):
    matrix = []
    seq = []
    y = fund
    if fund == 0:
        i = 1
        for _ in range(length):
            seq.append(y)
            i, y = y, i + y
    else:
        i = fund
        for _ in range(length):
            seq.append(i)
            i, y = y, i + y
    for note in seq:
        if note == 0:
            i = 1
            for _ in range(len(seq)):
                matrix.append(note)
                note, i = i, note + i
        else:
            i = 0
            for _ in range(len(seq)):
                matrix.append(note)
                i, note = note, i + note
    return [list(array) for array in np.array_split(np.array(matrix), len(seq))]

def overtone(fund, length):
    partial = 1
    overtones = []
    

if __name__ == '__main__':
    print(fibonacci(0, 5))