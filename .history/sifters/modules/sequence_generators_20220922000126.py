import numpy as np

def fibonacci(fund, length):
    i = 0
    y = fund
    seq = []
    # What if fund = 0
    for _ in range(length):
        seq.append(i)
        i, y = y, i + y
    return seq

def midi_to_freq(matrix):
    freq = []
    for row in matrix:
        for tone in row:
            a = 440
            freq.append((a / float(32)) * (2 ** ((tone - 9) / float(12))))
    return [list(array) for array in np.array_split(np.array(freq), len(row))]

# https://stackoverflow.com/a/62344771

# def to_sum_k(n, k):
#     if n == 1: 
#         return [ [k] ]
#     if n > k or n <= 0:
#         return []
#     res = []
#     for i in range(k):
#         sub_results = to_sum_k(n-1, k-i)
#         for sub in sub_results:
#             res.append(sub + [i])
#     return res

cache = {}
def to_sum_k(n, k):
    res = cache.get((n,k), [])
    if res: 
        return res

    if n == 1: 
        res  = [ [k] ]
    elif n > k or n <= 0:
        res = []
    else:
        for i in range(k):
            sub_results = to_sum_k(n-1, k-i)
            for sub in sub_results:
                res.append(sub + [i])
    cache[(n,k)] = res
    return res 

if __name__ == '__main__':
    print(to_sum_k(3,3)) 