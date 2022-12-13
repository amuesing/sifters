from music21 import *
import numpy as np

def binary(siev):
    bin = []
    if type(siev) == tuple:
        i = 0
        per = []
        obj = []
        for siv in siev:
            objects = sieve.Sieve(siv)
            obj.append(objects)
            per.append(objects.period())
        lcm = np.lcm.reduce(per)
        for o in obj:
            o.setZRange(0, lcm - 1)
            bin.append(o.segment(segmentFormat='binary'))
            i += 1
    else:
        obj = sieve.Sieve(siev)
        obj.setZRange(0, obj.period() - 1)
        bin.append(obj.segment(segmentFormat='binary'))
    return bin

def pitch_set(siev):
    # what if there are multiple sieves?
    set = sieve.PitchSieve(siev[0])
    period = set.sieveObject.period()
    set.sieveObject.setZRange(0, period - 1)
    intervals = set.sieveObject.segment()
    return intervals

# def formalize(bin, elem=1, index=0):
#     midi_key = [44, 60, 76, 80, 80, 80, 35, 35]
#     note_length = 0.25
    # iterations = len(bin)
    # offset = ([0] * len(bin)) * index
    # intro = offset + bin * (elem - index)
    # body = bin * iterations
    # return [intro + body, note_length, midi_key[index]]
    # return [bin, note_length, midi_key[index]]

if __name__ == '__main__':
    p_s = '((8@0|8@1|8@7)&(5@1|5@3))|((8@0|8@1|8@2)&5@0)|((8@5|8@6)&(5@2|5@3|5@4))|(8@3)|(8@4)|(8@1&5@2)|(8@6&5@1)', '((8@0|8@1|8@7)&(5@1|5@3))', '((8@0|8@1|8@2)&5@0)', '((8@5|8@6)&(5@2|5@3|5@4))', '(8@6&5@1)', '(8@3)', '(8@4)', '(8@1&5@2)'
    form = pitch_set(p_s)
    print(form)