def generate_fibonacci_matrix(fund, length):
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
    for z in seq:
        x = []
        if z == 0:
            i = 1
            for _ in range(len(seq)):
                x.append(z)
                z, i = i, z + i
        else:
            i = 0
            for _ in range(len(seq)):
                x.append(z)
                i, y = y, i + y
    matrix.append(x)
    return matrix