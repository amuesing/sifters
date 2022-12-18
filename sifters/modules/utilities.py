import pickle

def largest_prime_factor(n):
    return next(n // i for i in range(1, n) if n % i == 0 and is_prime(n // i))

def is_prime(m):
    return all(m % i for i in range(2, m - 1))
# https://www.w3resource.com/python-exerc

def load_pickle(path):
    return pickle.load(open(path, 'rb'))

def factorize(num):
    return [n for n in range(1, num + 1) if num % n == 0]
# https://stackoverflow.com/questions/47064885/list-all-factors-of-number