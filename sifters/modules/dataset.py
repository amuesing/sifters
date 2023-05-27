'''
Preprocesses MIDI files
'''

import music21
import mido
import pandas


from modules.composition import *


def load_midi(filename):
    midi_file = mido.MidiFile(f'data/mid/{filename}')
    print(midi_file)
    return midi_file


def parse_midi(midi_file):
    messages = {
        'Type': [],
        'Channel': [],
        'Note': [],
        'Pitch': [],
        'Velocity': [],
        'Time': [],
    }
    event_types = ['note_on', 'pitchwheel', 'note_off']

    # Iterate over all the tracks in the MIDI file
    for track in midi_file.tracks:
        
        # Iterate over all the events in the track
        for event in track:
            
            if event.type in ['note_on', 'note_off']:

                messages['Type'].append(event.type)
                messages['Channel'].append(event.channel)
                messages['Note'].append(event.note)
                messages['Pitch'].append(None)
                messages['Velocity'].append(event.velocity)
                messages['Time'].append(event.time)
                
            if event.type == 'pitchwheel':
                messages['Type'].append(event.type)
                messages['Channel'].append(event.channel)
                messages['Note'].append(None)
                messages['Pitch'].append(event.pitch)
                messages['Velocity'].append(None)
                messages['Time'].append(event.time)
                
    messages_dataframe = pandas.DataFrame.from_dict(messages, orient='index').T
    
    return messages_dataframe

                
            # Get the delta time value for the event
            # delta_time = event.time
            # Print the delta time value
            # print(delta_time)
                # if event.type == 'note_on':
                #     timestamp = event.time
                #     print(timestamp)
    # # Iterate over all the tracks in the MIDI file
    # for i, track in enumerate(midi_file.tracks):
    #     print(f"Track {i}: {track.name}")
    #     # Iterate over all the messages in the track
    #     for message in track:
    #         # If the message is a note_on or note_off event, print the note number and velocity
    #         if message.type in ['note_on', 'note_off']:
    #             print(f"Note: {message.note}, Velocity: {message.velocity}, On: {message.start}")
    
    print(messages)
    # events = pandas.DataFrame(messages)
    # events.to_csv('data/csv/parsed.csv')

def extract_chords(dataframe):
    
    filtered_dataframe = dataframe[dataframe['Note'].apply(lambda x: len(x) > 2)]
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