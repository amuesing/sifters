from modules.composition import Composition
from modules.textures.monophonic import Monophonic

import mido
import decimal
import functools
import pandas
import numpy
import math

class Score(Composition):
    
    
    def __init__(self, **kwargs):

        self.kwargs = kwargs
        self.normalized_numerators = numpy.array([self.normalize_numerator(arg, self.get_multiplier(arg)) for arg in self.kwargs.values()])
        self.multipliers = list(self.kwargs.values())[-1].get_least_common_multiple(self.normalized_numerators) // self.normalized_numerators
        self.ticks_per_beat = 480
        self.normalized_parts_data = self.normalize_periodicity()
        self.track_list = self.set_track_list()
        
        
    @staticmethod
    def get_multiplier(arg):

        # Compute the least common multiple of the denominators in the grid_history fractions
        lcd = functools.reduce(math.lcm, (fraction.denominator for fraction in arg.grid_history))
        
        # Divide the least common multiple by the denominator of each fraction in grid_history
        multipliers = [lcd // fraction.denominator for fraction in arg.grid_history]
        
        # Return the resulting list, indexed by the part_id of the argument minus one
        return multipliers[arg.part_id - 1]
    
    
    @staticmethod
    def normalize_numerator(arg, mult):

        return arg.grid_history[arg.part_id-1].numerator * mult
    
    
    def set_track_list(self):
        track_list = []
        
        for kwarg in self.kwargs.values():
            midi_track = mido.MidiTrack()
            # midi_track.append(mido.Message('program_change', program=0))
            midi_track.name = f'{kwarg.name}'
            track_list.append(midi_track)
            
        return track_list

        
    def normalize_periodicity(self):
        
        normalized_parts_data = []
        
        for arg, multiplier in zip(self.kwargs.values(), self.multipliers):
            # Create a list to store the original notes_data and the copies that will be normalized.
            duplicates = [arg.notes_data.copy()]
            
            # Calculate the length of one repetition.
            length_of_one_rep = decimal.Decimal(math.pow(arg.period, 2))

            # Iterate over the range of multipliers to create copies of notes_data.
            for i in range(multiplier):
                # Create a copy of notes_data.
                dataframe_copy = arg.notes_data.copy()
                grid = decimal.Decimal(arg.grid.numerator) / decimal.Decimal(arg.grid.denominator)
                
                # Adjust the Start column of the copy based on the length of one repitition and grid value.
                dataframe_copy['Start'] = dataframe_copy['Start'] + (round(length_of_one_rep * grid, 6) * i)
                
                # Append the copy to the duplicates list.
                duplicates.append(dataframe_copy)
            
            # Concatenate the duplicates list into a single dataframe.
            result = pandas.concat(duplicates)
            
            # Remove duplicate rows from the concatenated dataframe.
            result = result.drop_duplicates()
            
            # Append the normalized dataframe to the normalized_parts_data list.
            normalized_parts_data.append(result)
            
        # Store the normalized_parts_data in self.normalized_parts_data.
        return normalized_parts_data
    
    
    def set_midi_messages(self):
        
        messages_data = []

        def parse_pitch_data(dataframe):
            
            # Compute 'Pitch' and 'Note' columns for each row
            for index, row in dataframe.iterrows():
                pitch = round(row['Note'] - math.floor(row['Note']), 4)
                note = math.floor(row['Note'])
                dataframe.at[index, 'Note'] = note
                
                # Calculate Pitch value by multiplying the float by 4095.
                # 4095 equates to the number of bits in a semitone 'pitchwheel' message
                # There are 4096 total bits, and the Mido library numbers them 0-4095.
                dataframe.at[index, 'Pitch'] = pitch * 4095
            
            # Convert 'Note' column to integer data type
            dataframe['Note'] = dataframe['Note'].astype(int)
            dataframe['Pitch'] = dataframe['Pitch'].astype(int)
            
            # Return the updated dataframe
            return dataframe
        
    
        for part in self.normalized_parts_data:

            new_rows = []
            part = parse_pitch_data(part)

            for _, row in part.iterrows():
                part['Message'] = 'note_on'
                part['Time'] = 0
                
            for _, row in part.iterrows():
                new_rows.append(row)
                if row['Message'] == 'note_on':
                    if row['Pitch'] != 0.0:
                        pitchwheel_row = row.copy()
                        pitchwheel_row['Message'] = 'pitchwheel'
                        # Why us this creating a float and not an integer
                        # pitchwheel_row['Pitch'] = pitchwheel_row['Pitch'] * 4095
                        new_rows.append(pitchwheel_row)
                    note_off_row = row.copy()
                    note_off_row['Message'] = 'note_off'
                    note_off_row['Time'] = round(note_off_row['Duration'] * self.ticks_per_beat)
                    new_rows.append(note_off_row)
            
            ### THERE IS AN EASIER WAY TO DO THIS BY SIMPLY ASSIGNING THE STARTS OFFSET TO THE TIME OF THE FIRST NOTE_ON MESSAGE    
            # Check if the DataFrame begins with a note or a rest.
            # If the compostion begins with a rest, create a 'note_off' message that is equal to the duration of the rest.
            if part.iloc[0]['Start'] != 0.0:
                note_off_row = part.iloc[0].copy()
                note_off_row['Velocity'] = 0
                note_off_row['Note'] = 0
                note_off_row['Message'] = 'note_off'
                note_off_row['Duration'] = part.iloc[0]['Start']
                note_off_row['Time'] = round(note_off_row['Duration'] * self.ticks_per_beat)
                note_off_row['Start'] = 0.0
                new_rows.insert(0, note_off_row)
                
            messages_dataframe = pandas.DataFrame(new_rows)
            column_order = ['Start', 'Message', 'Note', 'Pitch', 'Velocity', 'Time']
            messages_dataframe = messages_dataframe.reindex(columns=column_order)
            messages_dataframe.reset_index(drop=True, inplace=True)
            
            messages_data.append(messages_dataframe)
            
            messages_data[0].to_csv('data/csv/messages.csv')
                        
            return messages_data
    
             
    def write_midi(self):
        
        messages_data = self.set_midi_messages()
        
        def csv_to_midi_messages(dataframe):

            messages = []
            for _, row in dataframe.iterrows():
                if row['Message'] == 'note_on':
                    messages.append(mido.Message('note_on', note=row['Note'], velocity=row['Velocity'], time=row['Time']))
                elif row['Message'] == 'pitchwheel':
                    messages.append(mido.Message('pitchwheel', pitch=row['Pitch'], time=row['Time']))
                elif row['Message'] == 'note_off':
                    messages.append(mido.Message('note_off', note=row['Note'], velocity=row['Velocity'], time=row['Time']))

            return messages
        
        # Create a new MIDI file object
        score = mido.MidiFile()

        # Set the ticks per beat resolution
        score.ticks_per_beat = self.ticks_per_beat

        # # Write method to determine TimeSignature
        time_signature = mido.MetaMessage('time_signature', numerator=5, denominator=4)
        self.track_list[0].append(time_signature)

        # Convert the CSV data to Note messages and PitchBend messages
        midi_messages = [csv_to_midi_messages(part) for part in messages_data]
        
        # Add the Tracks to the MIDI File
        for track in self.track_list:
            score.tracks.append(track)

        # Add the Note messages and PitchBend messages to the MIDI file
        for i, _ in enumerate(self.track_list):
            for message in midi_messages:
                for msg in message:
                    self.track_list[i].append(msg)

        # Write the MIDI file
        score.save('data/mid/score.mid')

    
    def combine_parts(self, *args):
        
        @staticmethod
        def get_max_duration(dataframe):
            
            # Update the 'End' column using a lambda function to set it to the maximum value if it's a list
            dataframe['Duration'] = dataframe['Duration'].apply(lambda x: max(x) if isinstance(x, list) else x)

            return dataframe
        
        @staticmethod
        def update_duration_value(dataframe):
            current_end = dataframe['Start'] + dataframe['Duration']
            next_start = dataframe['Start'].shift(-1)
            next_start.to_csv('data/csv/test.csv')
            print(next_start)


            # Replace None values with appropriate values for comparison
            next_start = next_start.fillna(float('inf'))
            end = numpy.minimum(next_start, current_end)
            end = end.apply(lambda x: decimal.Decimal(str(x)))
            dataframe['Start'] = dataframe['Start'].apply(lambda x: decimal.Decimal(str(x)))

            dataframe['Duration'] = end - dataframe['Start']
            dataframe = dataframe.iloc[:-1]
            return dataframe


        @staticmethod
        def expand_note_lists(dataframe):
            
            # Convert list values in Velocity column to single values.
            dataframe['Velocity'] = dataframe['Velocity'].apply(lambda x: x[0] if isinstance(x, list) else x)
                
            # Separate rows with list values in MIDI column from rows without.
            start_not_lists = dataframe[~dataframe['Note'].apply(lambda x: isinstance(x, list))]
            start_lists = dataframe[dataframe['Note'].apply(lambda x: isinstance(x, list))]
            
            # Expand rows with list values in MIDI column so that each row has only one value.
            start_lists = start_lists.explode('Note')
            start_lists = start_lists.reset_index(drop=True)
            
            # Concatenate rows back together and sort by start time.
            result = pandas.concat([start_not_lists, start_lists], axis=0, ignore_index=True)
            result.sort_values('Start', inplace=True)
            result.reset_index(drop=True, inplace=True)
            
            return result.drop_duplicates()
        
        
        @staticmethod
        def filter_first_match(objects, indices):
            
            updated_objects = []
            first_match_found = False
            
            # Loop over all objects in the list.
            for i, obj in enumerate(objects):
                
                # Check if the current index is in the indices list.
                if i in indices and not first_match_found:
                    
                    # If the current index is in the indices list and a match hasn't been found yet, add the object to the updated list.
                    updated_objects.append(obj)
                    first_match_found = True
                    
                # If the current index is not in the indices list, add the object to the updated list.
                elif i not in indices:
                    updated_objects.append(obj)
            
            # Return the updated list.
            return updated_objects

        # Get objects and indices for the parts to combine.
        objects = [self.kwargs[key] for key in args if key in self.kwargs]

        # objects = [self.kwargs.get(args[i]) for i, _ in enumerate(self.kwargs)]
        indices = [i for i, kwarg in enumerate(self.kwargs.keys()) if kwarg in args]
        
        # Combine the notes data from the selected parts.
        combined_notes_data = pandas.concat([self.normalized_parts_data[i] for i in indices])

        # Group notes by their start times.
        combined_notes_data = self.group_by_start(combined_notes_data)
        
        # Get the maximum end value for notes that overlap in time.
        combined_notes_data = get_max_duration(combined_notes_data)
        
        # Update end values for notes that overlap in time.
        combined_notes_data = update_duration_value(combined_notes_data)
        
        # Expand lists of MIDI values into individual rows.
        combined_notes_data = expand_note_lists(combined_notes_data)
        
        # If all parts are monophonic, further process the combined notes.
        if all(isinstance(obj, Monophonic) for obj in objects):

            combined_notes_data = self.group_by_start(combined_notes_data)
            
            combined_notes_data = self.get_closest_note(combined_notes_data)
            
            combined_notes_data = self.convert_lists_to_scalars(combined_notes_data)
            
            combined_notes_data = self.close_intervals(combined_notes_data)
            
            combined_notes_data = self.combine_consecutive_note_values(combined_notes_data)
            
            combined_notes_data = self.adjust_note_range(combined_notes_data)
            
        # Update track list to match the combined parts.
        self.track_list = filter_first_match(self.track_list, indices)
        
        # Filter notes data to match the combined parts and update it with the combined notes.
        filtered_notes_data = filter_first_match(self.normalized_parts_data, indices)
        filtered_notes_data[indices[0]] = combined_notes_data
        self.normalized_parts_data = filtered_notes_data
        
        # Remove the arguments for the combined parts from self.kwargs.
        for arg in args[1:]:
            del self.kwargs[arg]
            
        combined_notes_data.to_csv('data/csv/combined.csv')