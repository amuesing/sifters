import numpy as np

def invert_binary(binary):
    return 1 - binary

def reverse_binary(binary):
    return binary[::-1]

def stretch_binary(binary, factor):
    return np.repeat(binary, factor)

def shift_binary(binary, shift_amount):
    return np.roll(binary, shift_amount)