from music21 import *
from modules import utilities
from itertools import cycle
import pandas as pd
import numpy as np

def measure_zero(s):
    s.insert(0, metadata.Metadata())
    s.metadata.title = 'Sifters'
    s.metadata.composer = 'Ari Müsing'
    s.insert(0, instrument.UnpitchedPercussion())
    s.insert(0, clef.PercussionClef())
    s.insert(0, meter.TimeSignature('5/4'))
    s.insert(0, tempo.MetronomeMark('mid', 92, note.Note(type='quarter')))
    return s

def midi_pool(bin):
    midi_pool = []
    events = (bin.count(1))
    lpf_slice = slice(0, utilities.largest_prime_factor(events))
    # how to determine number of instrument elements present/distribution of elements
    # instruments = cycle([35, 44, 60, 76, 80][lpf_slice])
    instrument_pool = cycle([60,61,62,63,64][lpf_slice])
    for _ in range(events):
        midi_pool.append(next(instrument_pool))
    return midi_pool

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
    return utilities.remove_duplicates(pd.DataFrame(rows_list))

def csv_to_midi(df):
    elem = []
    result = {}
    part = stream.Score()
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
    return part.makeRests(fillGaps=True)

