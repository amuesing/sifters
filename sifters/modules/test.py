from music21 import *
import pandas as pd
from itertools import count

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