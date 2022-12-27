from music21 import *
import pandas as pd
from itertools import count

def csv_to_midi(df):
    # Create a music21 Part object
    part = stream.Part()
    values = []
    rows = []
    i = 0
    # # Iterate through the rows of the DataFrame
    # for _, row in df.iterrows():
    #     # Extract the pitch and duration data from the row
    #     midi = row['Midi']
    #     duration = row['Duration']
    #     offset = row['Offset']
    #     # how to find chords where offset == offset
    #     part.insert(offset, note.Note(midi=midi, quarterLength=duration))
    # part.insert(0, meter.TimeSignature('5/4'))
    # return part
    # for value in df['Offset']:
    #     values.append(value)
    # offset_values = set(float(x) for x in values)
    # infinite_count = count(1)
    # d = pd.DataFrame(df, index=[next(infinite_count)])
    # print(df.reindex([next(count(1))]))
    # for offset in offset_values:
    #     r = df.loc[df['Offset'] == offset]
        # create a note obect if there is one column in the dataframe
        # create a chord object if there is more than one column in the dataframe
        # d.loc[i] = r
        # i += 0
        # if len(r) == 1:
        #     # value = df.at[i, 'Midi']
        #     # for value in df['Midi']:
        #     #     if df.loc
        #     # Get the row with label 'Alice'
        #     # row = df.loc[i]
        #     print('note')
        # else:
        #     print('chord')
        # # print(r)
        # i += 1
    # print(df.reindex([next(infinite_counter)]))
    print(df)