import math
import itertools


def get_sin_oscillator(freq, sample_rate):
    increment = (2 * math.pi * freq)/ sample_rate
    return (math.sin(v) for v in itertools.count(start=0, step=increment))

