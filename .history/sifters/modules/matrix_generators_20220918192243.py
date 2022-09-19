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
    matrix = np.array([])
    seq = np.array([])
    y = fund
    if fund == 0:
        i = 1
        for _ in range(length):
            seq.append(seq, y)
            i, y = y, i + y
    # else:
    #     i = fund
    #     for _ in range(length):
    #         np.append(seq, i)
    #         i, y = y, i + y
    #     for z in seq:
    #         x = np.array([])
    #         if z == 0:
    #             i = 1
    #             for _ in range(len(seq)):
    #                 np.append(x, z)
    #                 z, i = i, z + i
    #         else:
    #             i = 0
    #             for _ in range(len(seq)):
    #                 np.append(x, z)
    #                 i, z = z, i + z
    #                 np.concatenate((matrix, x))
    return seq

if __name__ == '__main__':
    a = np.array([1,2,3,4])
    b = np.array([5,6,7,8])
    c = np.concatenate((a, b))
    print(c)