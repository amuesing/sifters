import numpy as np

from music21 import *

def largest_prime_factor(n):
    return next(n // i for i in range(1, n) if n % i == 0 and is_prime(n // i))

def is_prime(m):
    return all(m % i for i in range(2, m - 1))
# https://www.w3resource.com/python-exercises/challenges/1/python-challenges-1-exercise-35.php

###################################################

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

###################################################

def generate_part(pattern, midi_key, note_length, id):
    part = stream.Part(id='part{n}'.format(n=id))
    part.append(instrument.UnpitchedPercussion())
    period = len(pattern)
    numerator, denominator = largest_prime_factor(period), 4
    i = 0
    if id == 1:
            part.append(tempo.MetronomeMark('fast', 144, note.Note(type='quarter')))
    for point in pattern:
        if point == 1:
            part.insert(i * note_length, note.Note(midi=midi_key, quarterLength=note_length))
        i += 1
    part.insert(0, meter.TimeSignature('{n}/{d}'.format(n=numerator, d=denominator)))
    part.insert(0, clef.PercussionClef())
    part.makeMeasures(inPlace=True)
    part.makeRests(fillGaps=True, inPlace=True)
    return part

def generate_score(siev):
    s = stream.Score()
    id = 1
    sievs = initialize(siev)
    for siv in sievs:
        pattern, midi_key, note_length = siv[0], siv[1], siv[2]
        s.insert(0, generate_part(pattern, midi_key, note_length, id))
        id += 1
    s.insert(0, metadata.Metadata())
    s.metadata.title = 'Sifters'
    s.metadata.composer = 'Aarib Moosey'
    return s

###################################################

p_s = '((8@0|8@1|8@7)&(5@1|5@3))|((8@0|8@1|8@2)&5@0)|((8@5|8@6)&(5@2|5@3|5@4))|(8@3)|(8@4)|(8@1&5@2)|(8@6&5@1)', '((8@0|8@1|8@7)&(5@1|5@3))', '((8@0|8@1|8@2)&5@0)', '((8@5|8@6)&(5@2|5@3|5@4))', '(8@6&5@1)', '(8@3)', '(8@4)', '(8@1&5@2)'
psa = '((8@0|8@1|8@7)&(5@1|5@3))|((8@0|8@1|8@2)&5@0)|((8@5|8@6)&(5@2|5@3|5@4))|(8@3)|(8@4)|(8@1&5@2)|(8@6&5@1)'
sivs = '((8@0|8@1|8@7)&(5@1|5@3))', '((8@0|8@1|8@2)&5@0)', '((8@5|8@6)&(5@2|5@3|5@4))', '(8@6&5@1)', '(8@3)', '(8@4)', '(8@1&5@2)'

if __name__ == '__main__':
    c = generate_score(p_s)
    c.show('midi')
    print(c[1])
