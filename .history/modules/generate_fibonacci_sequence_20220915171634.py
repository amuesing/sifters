fundamental = 1
length = 12

def generate_fibonacci_sequence(fundamental, length):
    i = 0
    y = fundamental
    sequence = []
    for _ in range(length):
        sequence.append(i)
        i, y = y, i + y
    return sequence
    # print(r)
    # print(range)

print(generate_fibonacci_sequence(fundamental, length))

# for i in range(10):
#     print(1)
# print()
