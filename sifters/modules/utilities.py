import pickle
import pandas as pd
import numpy as np
from music21 import *

def load_pickle(path):
    return pickle.load(open(path, 'rb'))

def remove_duplicates(df):
    return df.drop_duplicates()

def sort_values(df, column_name):
    return df.sort_values(by = column_name)
    
def csv_to_midi(df):
    elem = []
    result = {}
    part = stream.Stream()
    for _, row in df.iterrows():
        offset = row['Offset']
        mid = row['Midi']
        elem.append([offset, int(mid)])
    for sublist in elem:
        if sublist[0] in result:
            result[sublist[0]].append(sublist[1])
        else:
            result[sublist[0]] = [sublist[1]]
    for offset, mid in result.items():
        if len(mid) > 1:
            part.insert(offset, chord.Chord(mid, quarterLength=0.25))
        else:
            part.insert(offset, note.Note(mid[0], quarterLength=0.25))
    return part

# https://medium.com/swlh/music21-pandas-and-condensing-sequential-data-1251515857a6
def generate_row(mus_object, part, midi=np.nan):
    d = {}
    d.update({'Offset': mus_object.offset,
            'Midi': midi})
    return d

def generate_df(score):
    parts = score.parts
    rows_list = []
    for part in parts:
        for _, elt in enumerate(part.flat
                .stripTies()
                .getElementsByClass(
            [note.Note, note.Rest, chord.Chord, bar.Barline])):
            if hasattr(elt, 'pitches'):
                pitches = elt.pitches
                for pitch in pitches:
                    rows_list.append(generate_row(elt, part, pitch.midi))
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
    lpf = largest_prime_factor(50)
    print(lpf)