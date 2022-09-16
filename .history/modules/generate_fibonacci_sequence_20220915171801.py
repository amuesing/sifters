fund = 1
length = 12

def generate_fibonacci_sequence(fund, length):
    i = 0
    y = fund
    seq= []
    # What if fund = 0
    for _ in range(length):
        seq.append(i)
        i, y = y, i + y
    return seq

print(generate_fibonacci_sequence(fund, length))

# for i in range(10):
#     print(1)
# print()
