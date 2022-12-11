from music21 import *
import numpy as np

def formalize(bin, elem, index=0):
    midi_key = [44, 60, 76, 80, 80, 80, 35, 35]
    note_length = 0.25
    # iterations = 100
    offset = ([0] * len(bin)) * index
    intro = offset + bin * (elem - index)
    body = bin * len(bin)
    return [intro + body, midi_key[index], note_length]

def initialize(siev):
    pat = []
    if type(siev) == tuple:
        i = 0
        per = []
        obj = []
        elem = len(siev)
        for siv in siev:
            objects = sieve.Sieve(siv)
            obj.append(objects)
            per.append(objects.period())
        lcm = np.lcm.reduce(per)
        for o in obj:
            o.setZRange(0, lcm - 1)
            bin = o.segment(segmentFormat='binary')
            form = formalize(bin, elem, i)
            pat.append(form)
            i += 1
    else:
        obj = sieve.Sieve(siev)
        obj.setZRange(0, obj.period() - 1)
        bin = obj.segment(segmentFormat='binary')
        pat.append(formalize(bin))
    return pat