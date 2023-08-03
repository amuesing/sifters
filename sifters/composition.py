import collections
import decimal
import fractions
import itertools
import math
import sqlite3

import mido
import music21
import numpy
import pandas
import tqdm


import utility

from textures import heterophonic, homophonic, monophonic, nonpitched, polyphonic

class Composition:
    
    def __init__(self, sieves):

        # Initialize an instance of the Utility class to call helper methods from.
        self.utility = utility.Utility()

        # Assign sieves argument to self.
        self.sieves = sieves

        # Initialize a period variable which will be assigned to an integer within the set_binary method.
        self.period = None

        self.ticks_per_beat = 480

        # Derive normalized binary list(s) from the given sieve(s).
        self.binary = self.set_binary(sieves)

        # Interpolate a dictionary which tracks the indicies of pattern changes within self.binary.
        self.changes = [[tupl[1] for tupl in sublist] for sublist in self.get_consecutive_count()]

        # Derive self-similar lists of integers based on the self.changes attribute.
        self.form = [[[num]*len(lst) for num in lst] for lst in self.changes]

        # Derive a list of metric grids based on the percent of change that each integer with self.changes represents.
        self.grids_set = self.set_grids()

        # Calculate the number of repeats needed to achieve parity between grids.
        self.repeats = self.set_repeats()

        # Generate contrapuntal textures derived from the binary, grids_set, and repeats attributes.
        self.texture_objects = self.set_texture_objects()

        self.combined_texture_dataframes = self.set_combined_texture_dataframes()


    # This function translates a list of sieves (intervals) into binary format. 
    def set_binary(self, sieves):
        # Inner function that takes in sieves and converts them to binary representation.
        def get_binary(sieves):
            binary = []  # Holds the binary representation of each sieve.
            periods = []  # Accumulates the periods of each sieve.
            objects = []  # Stores the Sieve objects generated from each sieve.

            # Loop over the sieves, convert each to a Sieve object, and store object and its period.
            for siev in sieves:
                obj = music21.sieve.Sieve(siev)  # Convert sieve to Sieve object.
                objects.append(obj)  # Add Sieve object to the objects list.
                periods.append(obj.period())  # Store the period of the Sieve object.

            # Calculate the least common multiple (LCM) of all periods. 
            # This LCM will be used as the shared period for all sieves in binary form.
            self.period = self.utility.get_least_common_multiple(periods)

            # Loop over the Sieve objects, adjust each object's Z range based on the LCM, 
            # and then convert each to its binary representation.
            for obj in objects:
                obj.setZRange(0, self.period - 1)  # Set Z range of Sieve object to [0, LCM - 1].
                binary.append(obj.segment(segmentFormat='binary'))  # Convert to binary and store.

            # Return the binary representation of all sieves.
            return binary

        # Convert the input sieves to binary and store the result.
        binary = get_binary(sieves)

        # Return the binary representation of all input sieves.
        return binary
    

    # This function computes the count of consecutive occurrences of the same element 
    # for each list in the attribute self.binary.
    def get_consecutive_count(self):

        result = []  # A placeholder to store consecutive counts for each binary list.

        # Iterate over each binary list stored in self.binary.
        for sieve in self.binary:
            # Using itertools.groupby, we group same, consecutive elements in the list.
            # From each group, we capture the element (key) and the length of the group
            # (indicating the count of consecutive occurrences of the element).
            # Each element and its consecutive count are stored as a tuple.
            consecutive_counts = [(key, len(list(group))) for key, group in itertools.groupby(sieve)]

            # We then add the tuples of element and consecutive count from the current list 
            # to the overall result list.
            result.append(consecutive_counts)

        # The function returns the result, which is a list of lists. Each sublist 
        # contains tuples, where each tuple represents an element and its consecutive count.
        return result


    # This function generates grids that illustrate the fractions of the period for each change in the self.changes list.
    def set_grids(self):
        # Inner function to compute the proportion of the period that each number in the list represents.
        def get_percent_of_period(lst):
            return [
                # Each number is converted to a decimal and divided by the period to compute the proportion.
                [
                    (decimal.Decimal(num) / decimal.Decimal(self.period)).quantize(decimal.Decimal('0.000')) 
                    for num in sub_lst
                ] 
                for sub_lst in lst
            ]

        # Inner function to transform a list of decimal numbers into fractions.
        def convert_decimal_to_fraction(decimal_list):
            return [
                # Each decimal number in the sublist is converted to a fraction.
                [fractions.Fraction(decimal_num) for decimal_num in sub_list]
                for sub_list in decimal_list
            ]

        # Inner function to eliminate duplicate fractions in each sublist while maintaining the original order.
        def get_unique_fractions(input_list):
            return [
                # Utilize OrderedDict to preserve order while removing duplicates.
                list(collections.OrderedDict.fromkeys(sub_list)) 
                for sub_list in input_list
            ]

        # Calculate the proportion of the period represented by each change.
        percent = get_percent_of_period(self.changes)

        # Convert the calculated proportions to fractions.
        grids = convert_decimal_to_fraction(percent)

        # Remove duplicates from each grid while keeping the original order.
        grids = get_unique_fractions(grids)
        
        # Return the grids containing unique fractions representing the proportion of period.
        return grids


    # This function computes the repetitions required for each fraction in the grids_set to equalize them.
    def set_repeats(self):
        # Inner function to standardize the numerators in the list of grids by transforming them to a shared denominator.
        def set_normalized_numerators(grids):
            normalized_numerators = []  # A list to store the numerators adjusted to the common denominator.

            # Iterate over each sublist in the grids.
            for sublist in grids:
                # Compute the least common multiple (LCM) of all denominators in the sublist.
                lcm = self.utility.get_least_common_multiple([fraction.denominator for fraction in sublist])
                
                # Normalize each fraction in the sublist by adjusting the numerator to the LCM, resulting in fractions with a common denominator.
                normalized_sublist = [(lcm // fraction.denominator) * fraction.numerator for fraction in sublist]
                
                # Add the normalized sublist to the list of standardized numerators.
                normalized_numerators.append(normalized_sublist)
            
            # Return the numerators normalized to the common denominator.
            return normalized_numerators

        # Standardize the numerators in the grids_set.
        normalized_numerators = set_normalized_numerators(self.grids_set)

        # Flatten the list of normalized numerators.
        flattened_list = self.utility.flatten_list(normalized_numerators)
        
        # Determine the least common multiple of all the normalized numerators.
        least_common_multiple = self.utility.get_least_common_multiple(flattened_list)

        # Prepare a list to store the required number of repetitions for each fraction.
        repeats = []
        
        # For each sublist in the normalized numerators,
        for sublist in normalized_numerators:
            # calculate the repetition for each fraction in the sublist by dividing the LCM by the normalized numerator.
            # The result indicates the number of repetitions needed to equalize the fractions.
            repeats_sublist = [least_common_multiple // num for num in sublist]
            
            # Add the repetition counts for the sublist to the main repeats list.
            repeats.append(repeats_sublist)

        # Return the list containing repetition counts for each fraction.
        return repeats


    # This function generates and manages texture objects based on various texture types.
    def set_texture_objects(self):
        # Establish a dictionary mapping texture types to their associated classes.
        textures = {
            'heterophonic': heterophonic.Heterophonic,
            'homophonic': homophonic.Homophonic,
            'monophonic': monophonic.Monophonic,
            'nonpitched': nonpitched.NonPitched,
            'polyphonic': polyphonic.Polyphonic,
        }
        
        # Organize source data for textures using binary representation, grids_set, and repeat values.
        source_data = [[bin_lst, *data] for bin_lst, grids, repeats in zip(self.binary, self.grids_set, self.repeats) for data in zip(grids, repeats)]
            
        # Generate instances of each texture type using the source data, and store them in a dictionary.
        return {name: {f'{name}_{i}': instance(data) for i, data in enumerate(source_data)} for name, instance in textures.items()}


    def set_combined_texture_dataframes(self):

        def get_max_duration(dataframe):

            # Update the 'End' column using a lambda function to set it to the maximum value if it's a list
            dataframe['Duration'] = dataframe['Duration'].apply(lambda x: max(x) if isinstance(x, list) else x)

            return dataframe
        

        def update_duration_value(dataframe):
            
            current_end = dataframe['Start'] + dataframe['Duration']
            next_start = dataframe['Start'].shift(-1)

            # Replace None values with appropriate values for comparison
            next_start = next_start.fillna(float('inf'))
            end = numpy.minimum(next_start, current_end)
            end = end.apply(lambda x: decimal.Decimal(str(x)))

            dataframe['Start'] = dataframe['Start'].apply(lambda x: decimal.Decimal(str(x)))

            dataframe['Duration'] = end - dataframe['Start']

            dataframe = dataframe.iloc[:-1]
            
            return dataframe
        

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
        

        # Function to process pitch data from a dataframe, splitting decimal notes into note and pitch values.
        def parse_pitch_data(dataframe):
            dataframe['Note'] = dataframe['Note'].apply(numpy.floor)
            dataframe['Pitch'] = ((dataframe['Note'] - dataframe['Note'].values) * 4095).astype(int)
            dataframe['Note'] = dataframe['Note'].astype(int)
            return dataframe


        def combine_dataframes(dataframes_list):

            # Combine the notes data from the selected parts.
            combined_notes_data = pandas.concat(dataframes_list)

            # Group notes by their start times.
            combined_notes_data = self.utility.group_by_start(combined_notes_data)

            # Get the maximum end value for notes that overlap in time.
            combined_notes_data = get_max_duration(combined_notes_data)

            # Update end values for notes that overlap in time.
            combined_notes_data = update_duration_value(combined_notes_data)

            # Expand lists of MIDI values into individual rows.
            combined_notes_data = expand_note_lists(combined_notes_data)

            # # If all parts are Monophonic, further process the combined notes to match Monophonic texture.
            # if all(isinstance(obj, monophonic.Monophonic) for obj in objects):

            #     combined_notes_data = self.group_by_start(combined_notes_data)
                
            #     combined_notes_data = self.get_closest_note(combined_notes_data)
                
            #     combined_notes_data = self.convert_lists_to_scalars(combined_notes_data)
                
            #     combined_notes_data = self.close_intervals(combined_notes_data)
                
            #     combined_notes_data = self.combine_consecutive_note_values(combined_notes_data)
                
            #     combined_notes_data = self.adjust_note_range(combined_notes_data)
            
            return combined_notes_data

        # Connect to SQLite database
        database_connection = sqlite3.connect(f'data/db/.{self.__class__.__name__}.db')
        cursor = database_connection.cursor()

        # Keep track of unique texture names
        unique_texture_names = set()

        # Loop through all texture objects, converting columns to numeric where possible and storing in SQLite
        for texture_object_dict in self.texture_objects.values():
            for texture_object in texture_object_dict.values():
                dataframe = texture_object.notes_data

                # Convert all possible numeric columns
                for column in dataframe.columns:
                    if dataframe[column].dtype == 'object':
                        try:
                            dataframe[column] = pandas.to_numeric(dataframe[column])
                        except ValueError:
                            pass

                # Add the texture name to the set of unique texture names
                unique_texture_names.add(texture_object.name)

                # Store this DataFrame as a table in SQLite, the table name incorporates the object name for identification later
                dataframe.to_sql(name=f"{texture_object.name}_{texture_object.part_id}", con=database_connection, if_exists='replace')

        # Now for each unique texture name, combine the tables
        for texture_name in unique_texture_names:

            # Retrieve the list of all tables with this texture_name
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '{texture_name}_%';")
            tables = cursor.fetchall()

            # Build the query to union all tables
            query = " UNION ALL ".join(f"SELECT * FROM {table[0]}" for table in tables)

            # Create the combined table for this texture_name
            cursor.execute(f"CREATE TABLE {texture_name}_combined AS {query};")

            # Get column names from one of the texture object dataframes (assuming all have same structure)
            texture_object = next(iter(self.texture_objects.values()))  # Get first texture_object_dict
            first_texture_object = next(iter(texture_object.values()))  # Get first texture_object
            column_names = first_texture_object.notes_data.columns.tolist()
            column_names.remove('Start')  # We are grouping by 'Start', so we don't want to concatenate it

            # Group rows in the combined table by 'Start' value
            group_query = f"""
            CREATE TABLE {texture_name}_grouped AS
            SELECT Start, 
            {', '.join(f"GROUP_CONCAT({column}) as {column}" for column in column_names)}
            FROM {texture_name}_combined
            GROUP BY Start;
            """
            cursor.execute(group_query)

        # Commit changes and close connection
        database_connection.commit()
        database_connection.close()

        # for texture_name, texture_type in tqdm.tqdm(self.texture_objects.items(), desc='Normalizing notes dataframes'):
        #     # Normalize the note data in each texture object.
        #     for object_name, texture_object in texture_type.items():

        #         # Calculate the length of a single repetition and the size of the grid.
        #         length_of_one_rep = decimal.Decimal(math.pow(self.period, 2))
        #         grid = decimal.Decimal(texture_object.grid.numerator) / decimal.Decimal(texture_object.grid.denominator)

        #         # Generate repeated sequences by duplicating the notes_data DataFrame.
        #         duplicates = [texture_object.notes_data] + [texture_object.notes_data.copy().assign(Start=lambda dataframe: dataframe.Start + round((length_of_one_rep * grid) * i, 6)) for i in range(texture_object.repeat)]

        #         # Merge all duplicates and eliminate duplicate rows.
        #         result = pandas.concat(duplicates).drop_duplicates()
        #         self.texture_objects[f'{texture_name}'][f'{object_name}'].notes_data = result

        # combined_dataframes = {}

        # for texture_name, texture_type in tqdm.tqdm(self.texture_objects.items(), desc='Combining notes dataframes'):

        #     dataframes_list = []

        #     for texture_object in texture_type.values():
        #         dataframes_list.append(texture_object.notes_data)

        #     combined_dataframes[f'{texture_name}'] = combine_dataframes(dataframes_list)

        # # Iterate through each texture object to prepare MIDI data in a DataFrame format.
        # for object_name, texture_dataframe in tqdm.tqdm(combined_dataframes.items(), desc='Interpolating MIDI messages'):
        #     part = parse_pitch_data(texture_dataframe)

        #     part['Message'] = 'note_on'
        #     part['Time'] = 0

        #     new_rows = [row for _, row in part.iterrows()]
        #     pitchwheel_rows = [row.copy() for _, row in part.iterrows() if row['Pitch'] != 0.0]
        #     note_off_rows = [row.copy() for _, row in part.iterrows()]

        #     # Include 'pitchwheel' MIDI message rows to new_rows list.
        #     for pitchwheel_row in pitchwheel_rows:
        #         pitchwheel_row['Message'] = 'pitchwheel'
        #         new_rows.append(pitchwheel_row)

        #     # Include 'note_off' MIDI message rows to new_rows list.
        #     for note_off_row in note_off_rows:
        #         note_off_row['Message'] = 'note_off'
        #         note_off_row['Time'] = round(note_off_row['Duration'] * self.ticks_per_beat)
        #         new_rows.append(note_off_row)

        #     # Account for non-zero start time of first note by adding a 'note_off' row at the beginning.
        #     if part.iloc[0]['Start'] != 0.0:
        #         note_off_row = part.iloc[0].copy()
        #         note_off_row['Velocity'] = 0
        #         note_off_row['Note'] = 0
        #         note_off_row['Message'] = 'note_off'
        #         note_off_row['Duration'] = part.iloc[0]['Start']
        #         note_off_row['Time'] = round(note_off_row['Duration'] * self.ticks_per_beat)
        #         note_off_row['Start'] = 0.0
        #         new_rows.insert(0, note_off_row)

        #     # Convert new_rows list to a DataFrame and set the preferred column order.
        #     messages_dataframe = pandas.DataFrame(new_rows)
        #     column_order = ['Start', 'Message', 'Note', 'Pitch', 'Velocity', 'Time']
        #     messages_dataframe = messages_dataframe.reindex(columns=column_order)
        #     messages_dataframe.reset_index(drop=True, inplace=True)

        #     combined_dataframes[f'{object_name}'] = messages_dataframe

        # return combined_dataframes

    # Return the constructed dictionary of texture objects.
    

        # def set_track_list(self):
        #     track_list = []
            
        #     for kwarg in self.kwargs.values():
        #         midi_track = mido.MidiTrack()
        #         # midi_track.append(mido.Message('program_change', program=0))
        #         midi_track.name = f'{kwarg.name}'
        #         track_list.append(midi_track)
                
        #     return track_list
        
        # @staticmethod
        # def filter_first_match(objects, indices):
            
        #     updated_objects = []
        #     first_match_found = False
            
        #     # Loop over all objects in the list.
        #     for i, obj in enumerate(objects):
                
        #         # Check if the current index is in the indices list.
        #         if i in indices and not first_match_found:
                    
        #             # If the current index is in the indices list and a match hasn't been found yet, add the object to the updated list.
        #             updated_objects.append(obj)
        #             first_match_found = True
                    
        #         # If the current index is not in the indices list, add the object to the updated list.
        #         elif i not in indices:
        #             updated_objects.append(obj)

        #     # Return the updated list.
        #     return updated_objects
            
        # # # Update track list to match the combined parts.
        # # self.track_list = filter_first_match(self.track_list, indices)
        
        # # Filter notes data to match the combined parts and update it with the combined notes.
        # filtered_notes_data = filter_first_match(self.normalized_parts_data, indices)
        # filtered_notes_data[indices[0]] = combined_notes_data
        # self.normalized_parts_data = filtered_notes_data
        
        # # Remove the arguments for the combined parts from self.kwargs.
        # for arg in args[1:]:
        #     del self.kwargs[arg]
        
        
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
    
    sieves = ['|'.join(sieves)]
        
    comp = Composition(sieves)

    # for i in comp.texture_objects.values():
    #     for j in i.values():
    #         print(j.notes_data)