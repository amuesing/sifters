'''
Preprocesses MIDI files
'''

import music21
import pretty_midi
import pandas


from modules.composition import *

def load_midi(filename):
    
    midi_file = pretty_midi.PrettyMIDI(f'data/midi/{filename}')
    
    return midi_file


def parse_midi(midi_file):
    notes_data = []
    
    for instrument in midi_file.instruments:
        
        for note in instrument.notes:
            
            notes_data.append({
                    'Velocity': note.velocity,
                    'MIDI': note.pitch,
                    'Start': round(note.start, 3), 
                    'End': round(note.end, 3)
                    })
    
    # Call group_by_start method (inherited from Composition class) on DataFrame.
    # Sort the DataFrame by 'Start' value using .sort_values
    return Composition.group_by_start_and_end(pandas.DataFrame(notes_data))
    # return pandas.DataFrame(notes_data)


def extract_chords(dataframe):
    
    filtered_dataframe = dataframe[dataframe['MIDI'].apply(lambda x: len(x) > 2)]
    return filtered_dataframe



def midi_to_pitch_class(dataframe):
    
    # Define a function to apply the modular 12 operation to a list of MIDI values
    def mod_12(midi_list):
        return [midi % 12 for midi in midi_list]
    
    # Apply the function to the MIDI column in the dataframe
    dataframe['Pitch Class'] = dataframe['MIDI'].apply(mod_12)
    
    return dataframe


def extract_single_occurrences(dataframe):
    
    unique_midi_lists = list(set([frozenset(x) for x in dataframe['Pitch Class']]))
    unique_midi_lists = [list(x) for x in unique_midi_lists]
    
    unique_dataframe = pandas.DataFrame(columns=dataframe.columns)

    for midi_list in unique_midi_lists:
        temp_dataframe = dataframe[dataframe['Pitch Class'].apply(lambda x: set(x) == set(midi_list))]
        unique_dataframe = pandas.concat([unique_dataframe, temp_dataframe.iloc[0:1]])

    return unique_dataframe



def chords_to_sieves(dataframe):
    
    sieves = []
    
    midi_data = dataframe['Pitch Class'].tolist()
    
    for i, _ in enumerate(midi_data):
        sieves.append(str(music21.sieve.CompressionSegment(midi_data[i])))
    
    dataframe['Sieves'] = sieves
    
    return dataframe