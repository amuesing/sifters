import collections
import decimal
import fractions
import itertools
import math
import sqlite3

import datetime
import mido
import music21
import numpy
import pandas
import tqdm

import utility

from textures import heterophonic, homophonic, monophonic, nonpitched, polyphonic

class Composition:
    
    def __init__(self, sieve):

        # Get the current timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Connect to SQLite database
        self.database_connection = sqlite3.connect(f'data/db/.{self.__class__.__name__}_{timestamp}.db')

        self.cursor = self.database_connection.cursor()

        # Initialize an instance of the Utility class to call helper methods from.
        self.utility = utility.Utility()

        # Assign sieves argument to self.
        self.sieve = sieve

        # Initialize a period variable which will be assigned to an integer within the set_binary method.
        self.period = None

        self.ticks_per_beat = 480

        self.scaling_factor = 100000

        # Derive normalized binary list(s) from the given sieve.
        self.binary = self.set_binary(sieve)

        # Interpolate a dictionary which tracks the indicies of pattern changes within self.binary.
        self.changes = [tupl[1] for tupl in self.get_consecutive_count()]

        # Derive self-similar lists of integers based on the self.changes attribute.
        self.form = [[num]*len(self.changes) for num in self.changes]

        # Derive a list of metric grids based on the percent of change that each integer with self.changes represents.
        self.grids_set = self.set_grids()

        # Calculate the number of repeats needed to achieve parity between grids.
        self.repeats = self.set_repeats()

        # Generate contrapuntal textures derived from the binary, grids_set, and repeats attributes.
        self.texture_objects = self.set_texture_objects()

        self.process_table_data()


    def set_binary(self, siev):
        obj = music21.sieve.Sieve(siev)  # Convert sieve to Sieve object.
        self.period = obj.period()  # Store the period of the Sieve object.
        obj.setZRange(0, self.period - 1)  # Set Z range of Sieve object to [0, LCM - 1].
        binary = obj.segment(segmentFormat='binary')  # Convert to binary and store.

        # Return the binary representation of sieve.
        return binary


    def get_consecutive_count(self):
        # Using itertools.groupby, we group same, consecutive elements in the list.
        # From each group, we capture the element (key) and the length of the group
        # (indicating the count of consecutive occurrences of the element).
        consecutive_counts = [(key, len(list(group))) for key, group in itertools.groupby(self.binary)]

        # The function returns the result, which is a single list containing tuples.
        # Each tuple represents an element and its consecutive count.
        return consecutive_counts

    
    # Inner function to compute the proportion of the period that each number in the list represents.
    def _get_percent_of_period(self, lst):
        return [
            (decimal.Decimal(num) / decimal.Decimal(self.period)).quantize(decimal.Decimal('0.000')) 
            for num in lst
        ]


    # Inner function to transform a list of decimal numbers into fractions.
    def _convert_decimal_to_fraction(self, decimal_list):
        return [fractions.Fraction(decimal_num) for decimal_num in decimal_list]


    # Inner function to eliminate duplicate fractions in each sublist while maintaining the original order.
    def _get_unique_fractions(self, input_list):
        return list(collections.OrderedDict.fromkeys(input_list))



    # This function generates grids that illustrate the fractions of the period for each change in the self.changes list.
    def set_grids(self):

        # Calculate the proportion of the period represented by each change.
        percent = self._get_percent_of_period(self.changes)

        # Convert the calculated proportions to fractions.
        grids = self._convert_decimal_to_fraction(percent)

        # Remove duplicates from each grid while keeping the original order.
        grids = self._get_unique_fractions(grids)
        
        # Return the grids containing unique fractions representing the proportion of period.
        return grids
    
    
    # Inner function to standardize the numerators in the list of grids by transforming them to a shared denominator.
    def _set_normalized_numerators(self, grids):
        # Compute the least common multiple (LCM) of all denominators in the list.
        lcm = self.utility.get_least_common_multiple([fraction.denominator for fraction in grids])
        
        # Normalize each fraction in the list by adjusting the numerator to the LCM.
        normalized_numerators = [(lcm // fraction.denominator) * fraction.numerator for fraction in grids]
        
        # Return the normalized numerators.
        return normalized_numerators


    # This function computes the repetitions required for each fraction in the grids_set to equalize them.
    def set_repeats(self):
        # Standardize the numerators in the grids_set.
        normalized_numerators = self._set_normalized_numerators(self.grids_set)
        
        # Determine the least common multiple of the normalized numerators.
        least_common_multiple = self.utility.get_least_common_multiple(normalized_numerators)

        # Calculate the repetition for each fraction by dividing the LCM by the normalized numerator.
        repeats = [least_common_multiple // num for num in normalized_numerators]

        # Return the repetition counts for each fraction.
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
            
        objects_dict = {}
        for key, instance in textures.items():
            objects_dict[key] = instance(self.binary)  # Directly pass the single binary list

        return objects_dict

    
    def _convert_and_store_dataframes(self):

        for texture_key, texture_object in self.texture_objects.items():

            dataframe = texture_object.notes_data
            dataframe = dataframe.apply(pandas.to_numeric, errors='ignore')
            dataframe.to_sql(name=f'{texture_key}', con=self.database_connection, if_exists='replace', index=False)


    def _generate_sql_commands(self):
        sql_commands = []

        # Query all table names
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        texture_names = [row[0] for row in self.cursor.fetchall()]

        for texture in texture_names:
            # Fetch column names from the current table
            self.cursor.execute(f'PRAGMA table_info("{texture}")')
            columns = [row[1] for row in self.cursor.fetchall()]
            # Exclude 'Start' and 'End' from the list
            columns = [col for col in columns if col not in ['Start', 'End']]
            columns_string = ', '.join([f'"{col}"' for col in columns])

            for grid, repeat in zip(self.grids_set, self.repeats):
                length_of_one_rep = int(math.pow(self.period, 2) * (grid * self.scaling_factor))
                new_table_name = f'{texture}_{grid * self.scaling_factor}'
                accumulative_value = 0

                select_statements = []
                for _ in range(repeat):
                    select_statement = f'''SELECT {columns_string}, 
                    "Start" * {grid * self.scaling_factor} + {accumulative_value} AS "Start", 
                    "End" * {grid * self.scaling_factor} + {accumulative_value} AS "End" FROM "{texture}"'''
                    select_statements.append(select_statement)
                    accumulative_value += length_of_one_rep

                union_all_statements = " UNION ALL ".join(select_statements)
                create_command = f'''
                CREATE TABLE "{new_table_name}" AS 
                {union_all_statements};
                '''
                sql_commands.append(create_command)
            
            # List of new tables to combine
            new_tables = [f'{texture}_{grid * self.scaling_factor}' for grid in self.grids_set]

            # Collect all SELECT statements into a list
            select_statements = [f'SELECT * FROM "{new_table}"' for new_table in new_tables]

            # Join the SELECT statements using UNION ALL and create the combined table
            combine_command = f'''CREATE TABLE "{texture}_temp" AS 
                                {" UNION ".join(select_statements)};'''
            sql_commands.append(combine_command)

            # Delete original table and rename the combined table to the original name
            sql_commands.append(f'DROP TABLE "{texture}";')
            sql_commands.append(f'ALTER TABLE "{texture}_temp" RENAME TO "{texture}";')

            # Drop the new tables as they are no longer needed
            for new_table in new_tables:
                sql_commands.append(f'DROP TABLE "{new_table}";')

            # Continue appending other SQL commands
            columns_with_end = columns + ["End"]
            group_query_parts = [f'GROUP_CONCAT("{column}") as "{column}"' for column in columns_with_end]
            group_query_body = ', '.join(group_query_parts)

            group_query = f'''
            CREATE TABLE "{texture}_grouped" AS
            SELECT Start, {group_query_body}
            FROM "{texture}"
            GROUP BY Start;
            '''
            sql_commands.append(group_query)

        return "\n".join(sql_commands)


        #     max_duration_query = f'''
        #     CREATE TABLE {table_name}_max_duration AS
        #     WITH max_durations AS (
        #         SELECT Start, MAX(Duration) as MaxDuration
        #         FROM {table_name}
        #         GROUP BY Start
        #     )
        #     SELECT g.Start, g.Velocity, g.Note, m.MaxDuration as Duration
        #     FROM {table_name}_grouped g
        #     JOIN max_durations m ON g.Start = m.Start;
        #     '''
        #     sql_commands.append(max_duration_query)

        #     create_table_query = f'''
        #     CREATE TABLE {table_name}_end_column (
        #         Start INTEGER, 
        #         End INTEGER, 
        #         Duration INTEGER,
        #         Velocity INTEGER, 
        #         Note TEXT
        #     );
        #     '''
        #     sql_commands.append(create_table_query)

        #     insert_data_query = f'''
        #     WITH ModifiedDurations AS (
        #         SELECT 
        #             Start,
        #             Velocity,
        #             Note,
        #             CASE 
        #                 WHEN LEAD(Start, 1, Start + Duration) OVER(ORDER BY Start) - Start < Duration THEN
        #                     LEAD(Start, 1, Start + Duration) OVER(ORDER BY Start) - Start
        #                 ELSE
        #                     Duration
        #             END as ModifiedDuration
        #         FROM {table_name}_max_duration
        #     )

        #     INSERT INTO {table_name}_end_column
        #     SELECT 
        #         Start,
        #         CASE 
        #             WHEN LEAD(Start, 1, NULL) OVER(ORDER BY Start) IS NULL THEN (Start + ModifiedDuration)
        #             WHEN (Start + ModifiedDuration) < LEAD(Start, 1, NULL) OVER(ORDER BY Start) THEN (Start + ModifiedDuration)
        #             ELSE LEAD(Start, 1, NULL) OVER(ORDER BY Start)
        #         END as End,
        #         ModifiedDuration,
        #         Velocity,
        #         Note
        #     FROM ModifiedDurations;
        #     '''
        #     sql_commands.append(insert_data_query)

        #     # Add the "End" column and update its values
        #     add_end_column_query = f"ALTER TABLE {table_name} ADD COLUMN End INTEGER;"
        #     sql_commands.append(add_end_column_query)

        #     update_end_column_query = f'''
        #     UPDATE {table_name}
        #     SET End = (
        #         SELECT End 
        #         FROM {table_name}_end_column
        #         WHERE {table_name}.Start = {table_name}_end_column.Start
        #     );
        #     '''
        #     sql_commands.append(update_end_column_query)

        #     # Remove rows with duplicate "Start" and "Note" values
        #     delete_duplicates_query = f'''
        #     DELETE FROM {table_name} 
        #     WHERE rowid NOT IN (
        #         SELECT MIN(rowid) 
        #         FROM {table_name} 
        #         GROUP BY Start, Note
        #     );
        #     '''
        #     sql_commands.append(delete_duplicates_query)

        #     # Delete the "Duration" column by recreating the table without it
        #     recreate_without_duration_query = f'''
        #     CREATE TABLE {table_name}_temp AS 
        #     SELECT Start, End, Note, Velocity 
        #     FROM {table_name};

        #     DROP TABLE {table_name};

        #     ALTER TABLE {table_name}_temp RENAME TO {table_name};
        #     '''
        #     sql_commands.append(recreate_without_duration_query)

        #     # Function to process pitch data from a dataframe, splitting decimal notes into note and pitch values.
        #     def parse_pitch_data(dataframe):
        #         dataframe['Note'] = dataframe['Note'].apply(numpy.floor)
        #         dataframe['Pitch'] = ((dataframe['Note'] - dataframe['Note'].values) * 4095).astype(int)
        #         dataframe['Note'] = dataframe['Note'].astype(int)
        #         return dataframe

        # return sql_commands
    
    
    def _execute_sql_commands(self, sql_commands):
        self.cursor.executescript(sql_commands)


    def _cleanup_tables(self, texture_names):
        for table_name in texture_names:
            self.cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '{table_name}_%' AND name != '{table_name}';")
            tables_to_delete = self.cursor.fetchall()
            for table in tables_to_delete:
                self.cursor.execute(f"DROP TABLE {table[0]};")
        self.database_connection.commit()
        self.database_connection.close()


    def process_table_data(self):
        self._convert_and_store_dataframes()
        sql_commands = self._generate_sql_commands()
        self._execute_sql_commands(sql_commands)
        # self._cleanup_tables(table_data)
        

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
        
        
if __name__ == '__main__':

    sieve = '''
            (((8@0|8@1|8@7)&(5@1|5@3))|
            ((8@0|8@1|8@2)&5@0)|
            ((8@5|8@6)&(5@2|5@3|5@4))|
            (8@6&5@1)|
            (8@3)|
            (8@4)|
            (8@1&5@2))
            '''
        
    comp = Composition(sieve)