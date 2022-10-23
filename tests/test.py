# transitions = ['60', '62', '54', '55', '60']
transitions = ['A', 'B', 'C', 'A']


def rank(c):
    return ord(c) - ord('A')

T = [rank(c) for c in transitions]

print(T)

# #create matrix of zeros

# M = [[0]*4 for _ in range(4)]

# for (i,j) in zip(T,T[1:]):
#     M[i][j] += 1

# #now convert to probabilities:
# for row in M:
#     n = sum(row)
#     if n > 0:
#         row[:] = [f/sum(row) for f in row]

# #print M:

# for row in M:
#     print(row)
