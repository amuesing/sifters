import pickle
import pandas as pd
import numpy as np
from music21 import *

def load_pickle(path):
    return pickle.load(open(path, 'rb'))

# https://medium.com/swlh/music21-pandas-and-condensing-sequential-data-1251515857a6
def generate_row(mus_object, part, pitch_class=np.nan):
    d = {}
    d.update({'id': mus_object.id,
              'Part Name': part.partName,
              'Offset': mus_object.offset,
              'Duration': mus_object.duration.quarterLength,
              'Type': type(mus_object),
              'Pitch Class': pitch_class})
    return d

def generate_df(score):
    parts = score.parts
    rows_list = []
    for part in parts:
        for index, elt in enumerate(part.flat
                .stripTies()
                .getElementsByClass(
            [note.Note, note.Rest, chord.Chord, bar.Barline])):
            if hasattr(elt, 'pitches'):
                pitches = elt.pitches
                for pitch in pitches:
                    rows_list.append(generate_row(elt, part, pitch.pitchClass))
            else:
                rows_list.append(generate_row(elt, part))
    return pd.DataFrame(rows_list)

# https://www.w3resource.com/python-exerc
def largest_prime_factor(n):
    if n == 1:
        return 1
    else:
        return next(n // i for i in range(1, n) if n % i == 0 and is_prime(n // i))

def is_prime(m):
    return all(m % i for i in range(2, m - 1))

# https://stackoverflow.com/questions/47064885/list-all-factors-of-number
def factorize(num):
    return [n for n in range(1, num + 1) if num % n == 0]

if __name__ == '__main__':
    # f = factorize(400)
    # f.reverse()
    # print(f)
    lpf = largest_prime_factor(50)
    print(lpf)