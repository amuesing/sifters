from modules import utilities
from itertools import cycle

def midi_pool(bin):
    midi_pool = []
    events = (bin.count(1))
    lpf_slice = slice(0, utilities.largest_prime_factor(events))
    # how to determine number of instrument elements present/distribution of elements
    instruments = cycle([35, 44, 60, 76, 80][lpf_slice])
    for _ in range(events):
        midi_pool.append(next(instruments))
    return midi_pool
