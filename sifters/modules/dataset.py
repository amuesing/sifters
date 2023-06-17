import music21
import mido
import decimal
import pandas

from modules.composition import *

class Dataset(Composition):
    
    
    def __init__(self, midi_file):
        self.midi_messages = self.parse_midi(midi_file)
    
    
    def parse_midi(self, filename):
        
        midi_file = mido.MidiFile(f'data/mid/{filename}')
        self.ticks_per_beat = midi_file.ticks_per_beat
        messages = []
        
        for track in midi_file.tracks:
            for event in track:
                if event.type in ['note_on', 'note_off']:
                    message = {
                        'Type': event.type,
                        'Channel': event.channel,
                        'Note': event.note,
                        'Pitch': '--',
                        'Velocity': event.velocity,
                        'Time': event.time
                    } 
                elif event.type == 'pitchwheel':
                    message = {
                        'Type': event.type,
                        'Channel': event.channel,
                        'Note': '--',
                        'Pitch': event.pitch,
                        'Velocity': '--',
                        'Time': event.time
                    }
                else:
                    continue  # Skip other event types if necessary
                    
                messages.append(message)
        
        messages_dataframe = pandas.DataFrame(messages)
        
        return messages_dataframe
    
    
    def calculate_start_value(self, dataframe):
        mask = dataframe['Type'].isin(['note_on', 'note_off'])
        dataframe.loc[mask, 'Duration'] = dataframe.loc[mask, 'Time'] / self.ticks_per_beat
        dataframe.loc[~mask, 'Duration'] = '--'  # Assign '--' to Duration where the mask is False
        ## HOW DO I CALCULATE START VALUE FOR EACH ROW, BASED ON DURATION?
        return dataframe


    def extract_chords(self, dataframe):
        ## use group by start method from composition class
        dataframe = self.group_by_start(dataframe)
        
        dataframe = dataframe[dataframe['Note'].apply(lambda x: len(x) > 2)]
        
        return dataframe


    @staticmethod
    def midi_to_pitch_class(dataframe):
        
        # Define a function to apply the modular 12 operation to a list of MIDI values
        def mod_12(midi_list):
            return [midi % 12 for midi in midi_list]
        
        # Apply the function to the MIDI column in the dataframe
        dataframe['Pitch Class'] = dataframe['MIDI'].apply(mod_12)
        
        return dataframe


    @staticmethod
    def extract_single_occurrences(dataframe):
        
        unique_midi_lists = list(set([frozenset(x) for x in dataframe['Pitch Class']]))
        unique_midi_lists = [list(x) for x in unique_midi_lists]
        
        unique_dataframe = pandas.DataFrame(columns=dataframe.columns)

        for midi_list in unique_midi_lists:
            temp_dataframe = dataframe[dataframe['Pitch Class'].apply(lambda x: set(x) == set(midi_list))]
            unique_dataframe = pandas.concat([unique_dataframe, temp_dataframe.iloc[0:1]])

        return unique_dataframe


    @staticmethod
    def chords_to_sieves(dataframe):
        
        sieves = []
        
        midi_data = dataframe['Pitch Class'].tolist()
        
        for i, _ in enumerate(midi_data):
            sieves.append(str(music21.sieve.CompressionSegment(midi_data[i])))
        
        dataframe['Sieves'] = sieves
        
        return dataframe