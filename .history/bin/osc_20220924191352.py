import math
import itertools


def get_sin_oscillator(freq, sample_rate):
    increment = (2 * math.pi * freq)/ sample_rate
    print_