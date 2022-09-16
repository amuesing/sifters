def generate_fibonacci_sequence(fund, length):
    i = 0
    y = fund
    seq= []
    # What if fund = 0
    for _ in range(length):
        seq.append(i)
        i, y = y, i + y
return seq