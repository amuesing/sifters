import numpy as np

def generate_fibonacci_matrix(fund, length):
    matrix = np.array([])
    seq = np.array([])
    y = fund
    if fund == 0:
        i = 1
        for _ in range(length):
            np.append(seq, y)
            i, y = y, i + y
    else:
        i = fund
        for _ in range(length):
            np.append(seq, i)
            i, y = y, i + y
    for z in seq:
        x = np.array([])
        if z == 0:
            i = 1
            for _ in range(len(seq)):
                np.append(x, z)
                z, i = i, z + i
        else:
            i = 0
            for _ in range(len(seq)):
                np.append(x, z)
                i, z = z, i + z
    np.concatenate(matrix, x)
    return matrix