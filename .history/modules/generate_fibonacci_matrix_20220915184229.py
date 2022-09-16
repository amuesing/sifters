def generate_fibonacci_matrix(fund, length):
    matrix = []
    seq = []
    y = fund
    if fund == 0:
        i = 1
        for _ in range(length):
            seq.append(y)
            i, y = y, i + y
    else
    print(seq)

generate_fibonacci_matrix(0, 5)