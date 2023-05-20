from modules.composition import Composition
from modules.textures.monophonic import Monophonic

import mido
import pretty_midi
import functools
import pandas
import numpy
import math

class Score(Composition):
    
    
    def __init__(self, **kwargs):

        self.kwargs = kwargs
        self.normalized_numerators = numpy.array([self.normalize_numerator(arg, self.get_multiplier(arg)) for arg in self.kwargs.values()])
        self.multipliers = list(self.kwargs.values())[-1].get_least_common_multiple(self.normalized_numerators) // self.normalized_numerators
        self.set_track_list()
        self.normalize_periodicity()
        self.get_on_and_off_messages()
        
        
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
            
        self.track_list = track_list

        
    def normalize_periodicity(self):
        normalized_parts_data = []
        
        for arg, multiplier in zip(self.kwargs.values(), self.multipliers):
            # Create a list to store the original notes_data and the copies that will be normalized.
            duplicates = [arg.notes_data.copy()]
            
            # Calculate the length of one repetition.
            length_of_one_rep = math.pow(arg.period, 2)
            
            # Iterate over the range of multipliers to create copies of notes_data.
            for i in range(multiplier):
                # Create a copy of notes_data.
                dataframe_copy = arg.notes_data.copy()
                
                # Adjust the Start column of the copy based on the length of one repitition and grid value.
                dataframe_copy['Start'] = round(dataframe_copy['Start'] + (length_of_one_rep * arg.grid) * i, 6)
                
                # Append the copy to the duplicates list.
                duplicates.append(dataframe_copy)
            
            # Concatenate the duplicates list into a single dataframe.
            result = pandas.concat(duplicates)
            
            # Remove duplicate rows from the concatenated dataframe.
            result = result.drop_duplicates()
            
            # Append the normalized dataframe to the normalized_parts_data list.
            normalized_parts_data.append(result)
        
        # Store the normalized_parts_data in self.normalized_parts_data.
        self.normalized_parts_data = normalized_parts_data
        self.normalized_parts_data[0].to_csv('data/csv/norm.csv')
    
    
    def get_on_and_off_messages(self):
        for part in self.normalized_parts_data:
            # no need to make a new dataframe, just update the original one with Message column
            new_rows = []
            for _, row in part.iterrows():
                part['Message'] = 'note_on'
            for _, row in part.iterrows():
                new_rows.append(row)
                if row['Message'] == 'note_on':
                    note_off_row = row.copy()
                    note_off_row['Message'] = 'note_off'
                    new_rows.append(note_off_row)
                    
            # Check if the DataFrame begins with a note or a rest.
            # If the compostion begins with a rest, create a 'note_off' message that is equal to the duration of the rest.
            if part.iloc[0]['Start'] == 0.0:
                note_off_row = part.iloc[0].copy()
                note_off_row['Velocity'] = 0
                note_off_row['MIDI'] = 0
                note_off_row['Message'] = 'note_off'
                note_off_row['Duration'] = part.iloc[0]['Start']
                note_off_row['Start'] = 0.0
                new_rows.insert(0, note_off_row)
            new_df = pandas.DataFrame(new_rows)
            new_df.reset_index(drop=True, inplace=True)
            new_df.to_csv('data/csv/note_on.csv')
            
                
    def write_score(self):
        # Create a new MIDI file object
        score = mido.MidiFile()

        # Set the ticks per beat resolution
        score.ticks_per_beat = 480

        # # Write method to determine TimeSignature
        time_sig = mido.MetaMessage('time_signature', numerator=5, denominator=4)
        self.track_list[0].append(time_sig)

        # Convert the CSV data to Note messages and PitchBend messages
        note_msgs = [self.csv_to_note_msg(part) for part in self.normalized_parts_data]
        bend_msgs = [self.csv_to_bend_msg(part) for part in self.normalized_parts_data]
        
        # Add the Tracks to the MIDI File
        for track in self.track_list:
            score.tracks.append(track)
        
        
        # # Add the Note messages and PitchBend messages to the MIDI file
        # for i, _ in enumerate(self.track_list):
        #     for msg in note_msgs:
        #         self.track_list[i].append(msg)
        # for msg in bend_msgs:
        #         self.track_list[i].append(msg)
                
        
        # Write the MIDI file
        # score.save('data/mid/score.mid')


    @staticmethod
    def csv_to_note_msg(dataframe):
        # print(dataframe)
        # dataframe['Duration'] = [round(row['End'] - row['Start'], 6) for _, row in dataframe.iterrows()]

        
        note_messages = [mido.Message('note_on',)]
        # dataframe.to_csv('duration.csv')
        # # Use a list comprehension to generate a list of Note messages from the input dataframe
        # # The list comprehension iterates over each row in the dataframe and creates a new Note message with the specified attributes
        # note_msgs = [mido.Message('note_on', note=int(row['MIDI']), velocity=int(row['Velocity']), time=int(row['Start']*480)) for _, row in dataframe.iterrows()]
        # note_off_msgs = [mido.Message('note_off', note=int(row['MIDI']), velocity=int(row['Velocity']), time=int(row['End']*480)) for _, row in dataframe.iterrows()]
        
        # # Return the list of Note messages
        # return note_msgs + note_off_msgs


    @staticmethod
    def csv_to_bend_msg(dataframe):
        if 'Pitch' in dataframe.columns:
            # Use a list comprehension to generate a list of PitchBend messages from the input dataframe
            # The list comprehension iterates over each row in the dataframe and creates a new PitchBend message with the specified attributes
            bend_msgs = [mido.Message('pitchwheel', pitch=int(8192 * row['Pitch']), time=int(row['Start']*480)) for _, row in dataframe[dataframe['Pitch'] != 0.0].iterrows()]
        else:
            # If the 'Pitch' column does not exist, create a list of PitchBend messages with default pitch values
            bend_msgs = [mido.Message('pitchwheel', pitch=0, time=int(row['Start']*480)) for _, row in dataframe.iterrows()]

        # Return the list of PitchBend messages
        return bend_msgs
    
    
    def combine_parts(self, *args):
        
        @staticmethod
        def get_max_end_value(dataframe):

            # Make a copy of the input dataframe to avoid modifying the original
            dataframe = dataframe.copy()
            
            # Update the 'End' column using a lambda function to set it to the maximum value if it's a list
            dataframe['End'] = dataframe['End'].apply(lambda x: max(x) if isinstance(x, list) else x)
            
            return dataframe
        
        
        @staticmethod
        def update_end_value(dataframe):

            # Make a copy of the input dataframe to avoid modifying the original
            dataframe = dataframe.copy()
            
            # Update the 'End' column using numpy to take the minimum value between the current 'End' value and 
            # the 'Start' value of the next row in the dataframe
            dataframe['End'] = numpy.minimum(dataframe['Start'].shift(-1), dataframe['End'])
            
            # Drop the last row of the dataframe since it's no longer needed
            dataframe = dataframe.iloc[:-1]
            
            return dataframe
            
            
        @staticmethod
        def expand_note_lists(dataframe):

            # Create a copy of the input dataframe to avoid modifying the original one.
            dataframe = dataframe.copy()
            
            # Convert list values in Velocity column to single values.
            dataframe['Velocity'] = dataframe['Velocity'].apply(lambda x: x[0] if isinstance(x, list) else x)
            
            # Convert list values in Pitch column to single values, if the column exists.
            if 'Pitch' in dataframe.columns:
                dataframe['Pitch'] = dataframe['Pitch'].apply(lambda x: x[0] if isinstance(x, list) else x)
                
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
            return result
        
        
        @staticmethod
        def filter_first_match(objects, indices):

            
            updated_objects = []
            first_match_found = False
            
            # Loop over all objects in the list
            for i, obj in enumerate(objects):
                # Check if the current index is in the indices list
                if i in indices and not first_match_found:
                    # If the current index is in the indices list and a match hasn't been found yet, add the object to the updated list
                    updated_objects.append(obj)
                    first_match_found = True
                # If the current index is not in the indices list, add the object to the updated list
                elif i not in indices:
                    updated_objects.append(obj)
            
            # Return the updated list
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
        combined_notes_data = get_max_end_value(combined_notes_data)
        
        # Update end values for notes that overlap in time.
        combined_notes_data = update_end_value(combined_notes_data)
        
        # Expand lists of MIDI values into individual rows.
        combined_notes_data = expand_note_lists(combined_notes_data)
        
        # If all parts are monophonic, further process the combined notes.
        if all(isinstance(obj, Monophonic) for obj in objects):
            combined_notes_data = self.group_by_start(combined_notes_data)
            combined_notes_data = self.get_lowest_note(combined_notes_data)
            combined_notes_data = self.check_and_close_intervals(combined_notes_data)
            combined_notes_data = self.adjust_note_range(combined_notes_data)
            combined_notes_data = self.combine_consecutive_note_values(combined_notes_data)
            combined_notes_data = self.convert_lists_to_scalars(combined_notes_data)
            
        # Update instrumentation to match the combined parts.
        self.instrumentation = filter_first_match(self.instrumentation, indices)
        
        # Filter notes data to match the combined parts and update it with the combined notes.
        filtered_notes_data = filter_first_match(self.normalized_parts_data, indices)
        filtered_notes_data[indices[0]] = combined_notes_data
        self.normalized_parts_data = filtered_notes_data
        
        # Remove the arguments for the combined parts from self.kwargs.
        for arg in args[1:]:
            del self.kwargs[arg]