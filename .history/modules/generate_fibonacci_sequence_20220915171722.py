fund = 1
leng = 12

def generate_fibonacci_sequence(fund, leng):
    i = 0
    y = fund
    sequence = []
    for _ in range(leng):
        sequence.append(i)
        i, y = y, i + y
    return sequence
    # print(r)
    # print(range)

print(generate_fibonacci_sequence(fund, leng))

# for i in range(10):
#     print(1)
# print()
