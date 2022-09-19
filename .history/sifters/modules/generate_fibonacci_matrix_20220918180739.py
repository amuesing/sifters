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
/
    return matrix