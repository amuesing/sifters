import numpy as np

def fibonacci(fund, length):
    i = 0
    y = fund
    seq = []
    # What if fund = 0
    for _ in range(length):
        seq.append(i)
        i, y = y, i + y
    return seq

def midi_to_freq(matrix):
    freq = []
    for row in matrix:
        for tone in row:
            a = 440
            freq.append((a / float(32)) * (2 ** ((tone - 9) / float(12))))
    return [list(array) for array in np.array_split(np.array(freq), len(row))]

if __name__ == '__main__':
    print(midi_to_freq([[60, 59, 79], [54, 55, 67]]))