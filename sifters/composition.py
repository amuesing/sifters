from textures import *
from utility import Utility

import music21
import decimal
import fractions
import decimal


class Composition:
    
    
    def __init__(self, sieves):

        # Assign sieves argument to self.
        self.sieves = sieves

        # Initialize an instance of the Utility class to call helper methods from.
        self.utility = Utility()

        # Initialize a period variable which will be assigned to an integer within the set_binary method.
        self.period = None

        # Derive normalized binary list(s) from the given sieve(s).
        self.binary = self.set_binary(sieves)

        # Interpolate a dictionary which tracks the indicies of pattern changes within self.binary.
        self.changes = [[tupl[1] for tupl in sublist] for sublist in self.get_consecutive_count()]

        # Derive self-similar lists of integers based on the self.changes attribute.
        self.form = self.distribute_changes(self.changes)

        # Derive a list of metric grids based on the percent of change that each integer with self.changes represents.
        self.grids_set = self.set_grids()

        # Calculate the number of repeats needed to achieve parity between grids.
        self.repeats = self.set_repeats()

        # Generate contrapuntal textures derived from the binary, grids_set, and repeats attributes.
        self.textures = self.set_textures()


    def set_binary(self, sieves):

        def get_binary(sieves):
             
            binary = []
            periods = []
            objects = []
            
            for siev in sieves:
                obj = music21.sieve.Sieve(siev)
                objects.append(obj)
                periods.append(obj.period())
                
            # Compute the least common multiple of the periods of the input sieves.
            self.period = self.utility.get_least_common_multiple(periods)
            
            # Set the Z range of each Sieve object and append its binary representation to the list.
            for obj in objects:
                obj.setZRange(0, self.period - 1)
                binary.append(obj.segment(segmentFormat='binary'))

            return binary
        
        # Convert the list of sets of intervals to their binary forms
        binary = get_binary(sieves)

        return binary
    

    def get_consecutive_count(self):
        
        lst = self.binary
        result = []  # List to store the consecutive counts for each original list.

        for sieve in lst:
            consecutive_counts = []  # List to store the consecutive counts for the current original list.
            consecutive_count = 1  # Initialize the count with 1 since the first element is always consecutive.
            current_num = sieve[0]  # Initialize the current number with the first element.

            # Iterate over the elements starting from the second one.
            for num in sieve[1:]:
                if num == current_num:  # If the current number is the same as the previous one.
                    consecutive_count += 1
                else:  # If the current number is different than the previous one.
                    consecutive_counts.append((current_num, consecutive_count))  # Store the number and its consecutive count.
                    consecutive_count = 1  # Reset the count for the new number.
                    current_num = num  # Update the current number.

            # Add the count for the last number.
            consecutive_counts.append((current_num, consecutive_count))

            # Add the consecutive counts for the current original list to the result.
            result.append(consecutive_counts)

        return result
    
    
    def distribute_changes(self, changes):
        
        structured_lists = []
        
        for lst in changes:
            
            sieve_layer = []
            
            for num in lst:
                sublist = lst.copy() # Create a copy of the original list
                
                repeated_list = []
                
                for _ in range(num):
                    repeated_list.append(sublist) # Append the elements of sublist to repeated_list
                    
                sieve_layer.append(repeated_list)
                
            structured_lists.append(sieve_layer)
        
        return structured_lists
    

    def set_grids(self):


        def get_percent_of_period(lst):

            percent_of_period = [[(decimal.Decimal(num) / decimal.Decimal(self.period)).quantize(decimal.Decimal('0.000')) for num in l] for l in lst]

            return percent_of_period


        def convert_decimal_to_fraction(decimal_list):
            
            fraction_list = []

            for sublist in decimal_list:
                fraction_sublist = []
                
                for decimal in sublist:
                    fraction = fractions.Fraction(decimal)
                    fraction_sublist.append(fraction)
                    
                fraction_list.append(fraction_sublist)

            return fraction_list
        
        
        def get_unique_fractions(input_list):
            
            unique_fractions = []
            
            for sublist in input_list:
                
                unique_sublist = []
                unique_set = set()
                
                for fraction in sublist:
                    fraction_str = str(fraction)
                    
                    if fraction_str not in unique_set:
                        unique_set.add(fraction_str)
                        unique_sublist.append(fraction)
                
                unique_fractions.append(unique_sublist)
            
            return unique_fractions
            

        percent = get_percent_of_period(self.changes)
        
        grids = convert_decimal_to_fraction(percent)
        
        grids = get_unique_fractions(grids)
        
        return grids
    

    def set_repeats(self):

        def set_normalized_numerators(grids):
            
            # Extract the numerators from each list of Fraction objects.
            numerators = [[fraction.numerator for fraction in sublist] for sublist in grids]

            # Extract the denominators from each list of Fraction objects.
            denominators = [[fraction.denominator for fraction in sublist] for sublist in grids]
            
            # Find the least common multiple among denominators.
            least_common_denominator = self.utility.get_least_common_multiple(denominators)

            # Calculate the multiplier for each numerator based on the Least Common Denominator.
            multipliers = [[least_common_denominator // fraction.denominator for fraction in sublist] for sublist in grids]

            # Calculate the numerator of each fraction by multiplying each numerator by it's corresponding multiplier.
            normalized_numerators = [[num * mult for num, mult in zip(num_list, mult_list)] for num_list, mult_list in zip(numerators, multipliers)]

            return normalized_numerators

        # Normalize numerators across Fraction objects which comprise the Composition's grid_set attribute. 
        normalized_numerators = set_normalized_numerators(self.grids_set)

        flattened_list = self.utility.flatten_list(normalized_numerators)

        least_common_multiple = self.utility.get_least_common_multiple(flattened_list)

        # Initialize a list to contain integers which represent the number of repeats needed for normalization within a list.
        repeats = []

        # Calculate Least Common Multiple among normalized_numerators and calculate the multiplier needed for normalization.
        for lst in normalized_numerators:

            repeats.append([least_common_multiple // num for num in lst])

        return repeats
    

    def set_textures(self):

        textures = {
            'heterophonic': heterophonic.Heterophonic,
            'homophonic': homophonic.Homophonic,
            'monophonic': monophonic.Monophonic,
            'nonpitched': nonpitched.NonPitched,
            'polyphonic': polyphonic.Polyphonic,
            }
        
        source_data = []

        for bin_lst, grids, repeats in zip(self.binary, self.grids_set, self.repeats):
            for data in zip(grids, repeats):
                source_data.append([bin_lst, *data])

        texture_objects = {
            'heterophonic': {},
            'homophonic': {},
            'monophonic': {},
            'nonpitched': {},
            'polyphonic': {},
        }

        for texture_name, texture_instance in textures.items():
            for i, data in enumerate(source_data):
                texture_objects[f'{texture_name}'][f'{texture_name}_{i}'] = texture_instance(data)

        return texture_objects

######

    # def set_track_list(self):
    #     track_list = []
        
    #     for kwarg in self.kwargs.values():
    #         midi_track = mido.MidiTrack()
    #         # midi_track.append(mido.Message('program_change', program=0))
    #         midi_track.name = f'{kwarg.name}'
    #         track_list.append(midi_track)
            
    #     return track_list
    
    # def normalize_periodicity(self):
    
    #     normalized_parts_data = []
        
    #     for arg, multiplier in zip(self.kwargs.values(), self.multipliers):
    #         # Create a list to store the original notes_data and the copies that will be normalized.
    #         duplicates = [arg.notes_data.copy()]
            
    #         # Calculate the length of one repetition.
    #         length_of_one_rep = decimal.Decimal(math.pow(arg.period, 2))

    #         # Iterate over the range of multipliers to create copies of notes_data.
    #         for i in range(multiplier):
    #             # Create a copy of notes_data.
    #             dataframe_copy = arg.notes_data.copy()
    #             grid = decimal.Decimal(arg.grid.numerator) / decimal.Decimal(arg.grid.denominator)
                
    #             # Adjust the Start column of the copy based on the length of one repitition and grid value.
    #             dataframe_copy['Start'] = dataframe_copy['Start'] + round((length_of_one_rep * grid) * i, 6)

                
    #             # Append the copy to the duplicates list.
    #             duplicates.append(dataframe_copy)
            
    #         # Concatenate the duplicates list into a single dataframe.
    #         result = pandas.concat(duplicates)
            
    #         # Remove duplicate rows from the concatenated dataframe.
    #         result = result.drop_duplicates()
            
    #         # Append the normalized dataframe to the normalized_parts_data list.
    #         normalized_parts_data.append(result)
            
    #     # Store the normalized_parts_data in self.normalized_parts_data.
    #     return normalized_parts_data
    
    
    # def set_midi_messages(self):
        
    #     messages_data = []

    #     def parse_pitch_data(dataframe):
            
    #         # Compute 'Pitch' and 'Note' columns for each row
    #         for index, row in dataframe.iterrows():
    #             pitch = round(row['Note'] - math.floor(row['Note']), 4)
    #             note = math.floor(row['Note'])
    #             dataframe.at[index, 'Note'] = note
                
    #             # Calculate Pitch value by multiplying the float by 4095.
    #             # 4095 equates to the number of bits in a semitone 'pitchwheel' message
    #             # There are 4096 total bits, and the Mido library numbers them 0-4095.
    #             dataframe.at[index, 'Pitch'] = pitch * 4095
            
    #         # Convert 'Note' column to integer data type
    #         dataframe['Note'] = dataframe['Note'].astype(int)
    #         dataframe['Pitch'] = dataframe['Pitch'].astype(int)
            
    #         # Return the updated dataframe
    #         return dataframe
        
    
    #     for part in self.normalized_parts_data:

    #         new_rows = []
    #         part = parse_pitch_data(part)

    #         for _, row in part.iterrows():
    #             part['Message'] = 'note_on'
    #             part['Time'] = 0
                
    #         for _, row in part.iterrows():
    #             new_rows.append(row)
    #             if row['Message'] == 'note_on':
    #                 if row['Pitch'] != 0.0:
    #                     pitchwheel_row = row.copy()
    #                     pitchwheel_row['Message'] = 'pitchwheel'
    #                     # Why us this creating a float and not an integer
    #                     # pitchwheel_row['Pitch'] = pitchwheel_row['Pitch'] * 4095
    #                     new_rows.append(pitchwheel_row)
    #                 note_off_row = row.copy()
    #                 note_off_row['Message'] = 'note_off'
    #                 note_off_row['Time'] = round(note_off_row['Duration'] * self.ticks_per_beat)
    #                 new_rows.append(note_off_row)
            
    #         ### THERE IS AN EASIER WAY TO DO THIS BY SIMPLY ASSIGNING THE STARTS OFFSET TO THE TIME OF THE FIRST NOTE_ON MESSAGE    
    #         # Check if the DataFrame begins with a note or a rest.
    #         # If the compostion begins with a rest, create a 'note_off' message that is equal to the duration of the rest.
    #         if part.iloc[0]['Start'] != 0.0:
    #             note_off_row = part.iloc[0].copy()
    #             note_off_row['Velocity'] = 0
    #             note_off_row['Note'] = 0
    #             note_off_row['Message'] = 'note_off'
    #             note_off_row['Duration'] = part.iloc[0]['Start']
    #             note_off_row['Time'] = round(note_off_row['Duration'] * self.ticks_per_beat)
    #             note_off_row['Start'] = 0.0
    #             new_rows.insert(0, note_off_row)
                
    #         messages_dataframe = pandas.DataFrame(new_rows)
    #         column_order = ['Start', 'Message', 'Note', 'Pitch', 'Velocity', 'Time']
    #         messages_dataframe = messages_dataframe.reindex(columns=column_order)
    #         messages_dataframe.reset_index(drop=True, inplace=True)
            
    #         messages_data.append(messages_dataframe)
                        
    #         return messages_data
    
             
    # def write_midi(self):
        
    #     messages_data = self.set_midi_messages()
        
    #     def csv_to_midi_messages(dataframe):

    #         messages = []
    #         for _, row in dataframe.iterrows():
    #             if row['Message'] == 'note_on':
    #                 messages.append(mido.Message('note_on', note=row['Note'], velocity=row['Velocity'], time=row['Time']))
    #             elif row['Message'] == 'pitchwheel':
    #                 messages.append(mido.Message('pitchwheel', pitch=row['Pitch'], time=row['Time']))
    #             elif row['Message'] == 'note_off':
    #                 messages.append(mido.Message('note_off', note=row['Note'], velocity=row['Velocity'], time=row['Time']))

    #         return messages
        
    #     # Create a new MIDI file object
    #     score = mido.MidiFile()

    #     # Set the ticks per beat resolution
    #     score.ticks_per_beat = self.ticks_per_beat

    #     # # Write method to determine TimeSignature
    #     time_signature = mido.MetaMessage('time_signature', numerator=5, denominator=4)
    #     self.track_list[0].append(time_signature)

    #     # Convert the CSV data to Note messages and PitchBend messages
    #     midi_messages = [csv_to_midi_messages(part) for part in messages_data]
        
    #     # Add the Tracks to the MIDI File
    #     for track in self.track_list:
    #         score.tracks.append(track)

    #     # Add the Note messages and PitchBend messages to the MIDI file
    #     for i, _ in enumerate(self.track_list):
    #         for message in midi_messages:
    #             for msg in message:
    #                 self.track_list[i].append(msg)

    #     # Write the MIDI file
    #     score.save('data/mid/score.mid')

    
    # def combine_parts(self, *args):
        
    #     @staticmethod
    #     def get_max_duration(dataframe):

    #         # Update the 'End' column using a lambda function to set it to the maximum value if it's a list
    #         dataframe['Duration'] = dataframe['Duration'].apply(lambda x: max(x) if isinstance(x, list) else x)

    #         return dataframe
        
        
    #     @staticmethod
    #     def update_duration_value(dataframe):
            
    #         current_end = dataframe['Start'] + dataframe['Duration']
    #         next_start = dataframe['Start'].shift(-1)

    #         # Replace None values with appropriate values for comparison
    #         next_start = next_start.fillna(float('inf'))
    #         end = numpy.minimum(next_start, current_end)
    #         end = end.apply(lambda x: decimal.Decimal(str(x)))

    #         dataframe['Start'] = dataframe['Start'].apply(lambda x: decimal.Decimal(str(x)))

    #         dataframe['Duration'] = end - dataframe['Start']

    #         dataframe = dataframe.iloc[:-1]
            
    #         return dataframe


    #     @staticmethod
    #     def expand_note_lists(dataframe):
            
    #         # Convert list values in Velocity column to single values.
    #         dataframe['Velocity'] = dataframe['Velocity'].apply(lambda x: x[0] if isinstance(x, list) else x)
                
    #         # Separate rows with list values in MIDI column from rows without.
    #         start_not_lists = dataframe[~dataframe['Note'].apply(lambda x: isinstance(x, list))]
    #         start_lists = dataframe[dataframe['Note'].apply(lambda x: isinstance(x, list))]
            
    #         # Expand rows with list values in MIDI column so that each row has only one value.
    #         start_lists = start_lists.explode('Note')
    #         start_lists = start_lists.reset_index(drop=True)
            
    #         # Concatenate rows back together and sort by start time.
    #         result = pandas.concat([start_not_lists, start_lists], axis=0, ignore_index=True)
    #         result.sort_values('Start', inplace=True)
    #         result.reset_index(drop=True, inplace=True)
            
    #         return result.drop_duplicates()
        
        
    #     @staticmethod
    #     def filter_first_match(objects, indices):
            
    #         updated_objects = []
    #         first_match_found = False
            
    #         # Loop over all objects in the list.
    #         for i, obj in enumerate(objects):
                
    #             # Check if the current index is in the indices list.
    #             if i in indices and not first_match_found:
                    
    #                 # If the current index is in the indices list and a match hasn't been found yet, add the object to the updated list.
    #                 updated_objects.append(obj)
    #                 first_match_found = True
                    
    #             # If the current index is not in the indices list, add the object to the updated list.
    #             elif i not in indices:
    #                 updated_objects.append(obj)
            
    #         # Return the updated list.
    #         return updated_objects

    #     # Get objects and indices for the parts to combine.
    #     objects = [self.kwargs[key] for key in args if key in self.kwargs]

    #     # objects = [self.kwargs.get(args[i]) for i, _ in enumerate(self.kwargs)]
    #     indices = [i for i, kwarg in enumerate(self.kwargs.keys()) if kwarg in args]
        
    #     # Combine the notes data from the selected parts.
    #     combined_notes_data = pandas.concat([self.normalized_parts_data[i] for i in indices])

    #     # Group notes by their start times.
    #     combined_notes_data = self.group_by_start(combined_notes_data)
        
    #     # Get the maximum end value for notes that overlap in time.
    #     combined_notes_data = get_max_duration(combined_notes_data)

    #     # Update end values for notes that overlap in time.
    #     combined_notes_data = update_duration_value(combined_notes_data)
        
    #     # Expand lists of MIDI values into individual rows.
    #     combined_notes_data = expand_note_lists(combined_notes_data)
        
    #     # If all parts are Monophonic, further process the combined notes to match Monophonic texture.
    #     if all(isinstance(obj, Monophonic) for obj in objects):

    #         combined_notes_data = self.group_by_start(combined_notes_data)
            
    #         combined_notes_data = self.get_closest_note(combined_notes_data)
            
    #         combined_notes_data = self.convert_lists_to_scalars(combined_notes_data)
            
    #         combined_notes_data = self.close_intervals(combined_notes_data)
            
    #         combined_notes_data = self.combine_consecutive_note_values(combined_notes_data)
            
    #         combined_notes_data = self.adjust_note_range(combined_notes_data)
            
    #     # Update track list to match the combined parts.
    #     self.track_list = filter_first_match(self.track_list, indices)
        
    #     # Filter notes data to match the combined parts and update it with the combined notes.
    #     filtered_notes_data = filter_first_match(self.normalized_parts_data, indices)
    #     filtered_notes_data[indices[0]] = combined_notes_data
    #     self.normalized_parts_data = filtered_notes_data
        
    #     # Remove the arguments for the combined parts from self.kwargs.
    #     for arg in args[1:]:
    #         del self.kwargs[arg]
        
        
if __name__ == '__main__':
    
    sieves = [
    
    '((8@0|8@1|8@7)&(5@1|5@3))', 
    '((8@0|8@1|8@2)&5@0)',
    '((8@5|8@6)&(5@2|5@3|5@4))',
    '(8@6&5@1)',
    '(8@3)',
    '(8@4)',
    '(8@1&5@2)'
    
    ]
    
    # sieves = ['|'.join(sieves)]
        
    comp = Composition(sieves)