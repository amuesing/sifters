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


    def _generate_sql_for_duration_values(self, texture, columns_string):
        duration_values = [grid * self.scaling_factor for grid in self.grids_set]
        length_of_reps = [int(math.pow(self.period, 2) * duration) for duration in duration_values]

        table_commands = {}
        for duration_value, length_of_one_rep, repeat in zip(duration_values, length_of_reps, self.repeats):
            table_name = f"{texture}_{duration_value}"
            table_commands[table_name] = self._generate_union_all_statements(texture, columns_string, duration_value, length_of_one_rep, repeat)
        
        return table_commands
    

    def _generate_union_all_statements(self, texture, columns_string, duration_value, length_of_one_rep, repeat):
        accumulative_value = 0
        select_statements = []

        for _ in range(repeat):
            select_statements.append(f'''
            SELECT {columns_string}, 
            "Start" * {duration_value} + {accumulative_value} AS "Start",
            "Duration" * {duration_value} AS "Duration"
            FROM "{texture}"''')
            accumulative_value += length_of_one_rep
        
        return " UNION ALL ".join(select_statements)
    

    def _generate_combined_commands(self, texture, duration_values):
        new_tables = [f'{texture}_{grid * self.scaling_factor}' for grid in duration_values]
        select_statements = [f'SELECT * FROM "{new_table}"' for new_table in new_tables]
        return f'''CREATE TABLE "{texture}_combined" AS 
                            {" UNION ".join(select_statements)};'''
    

    def _generate_grouped_commands(self, texture, columns):
        group_query_parts = [f'GROUP_CONCAT("{column}") as "{column}"' for column in columns]
        group_query_parts.append('GROUP_CONCAT("Duration") AS "Duration"')
        group_query_body = ', '.join(group_query_parts)
        return f'''
        CREATE TABLE "{texture}_grouped" AS
        SELECT Start, {group_query_body}
        FROM "{texture}_combined"
        GROUP BY Start;
        '''
    

    def _generate_max_duration_command(self, texture):
        return f'''
        CREATE TABLE "{texture}_max_duration" AS
        WITH max_durations AS (
            SELECT Start, MAX(Duration) as MaxDuration
            FROM "{texture}_combined"
            GROUP BY Start
        )
        SELECT c.Start, c.Velocity, c.Note, m.MaxDuration as Duration
        FROM "{texture}_combined" c
        LEFT JOIN max_durations m ON c.Start = m.Start;
        '''


    def _generate_drop_duplicates_command(self, texture):
        return f'''
        CREATE TABLE temp_table AS
        SELECT DISTINCT * FROM "{texture}_max_duration";
        DROP TABLE "{texture}_max_duration";
        ALTER TABLE temp_table RENAME TO "{texture}_max_duration";
        '''


    def _generate_create_end_table_command(self, texture):
        return f'''
        CREATE TABLE "{texture}_end_column" (
            Start INTEGER, 
            End INTEGER, 
            Duration INTEGER,
            Velocity INTEGER, 
            Note TEXT
        );
        '''


    def _generate_insert_end_data_command(self, texture):
        return f'''
        WITH ModifiedDurations AS (
            SELECT 
                Start,
                Velocity,
                Note,
                Duration as ModifiedDuration
            FROM "{texture}_max_duration"
        ),
        DistinctEnds AS (
            SELECT
                Start,
                COALESCE(LEAD(Start, 1) OVER(ORDER BY Start), Start + ModifiedDuration) AS End
            FROM (SELECT DISTINCT Start, ModifiedDuration FROM ModifiedDurations) as distinct_starts
        )
        INSERT INTO "{texture}_end_column"
        SELECT 
            m.Start,
            d.End,
            m.ModifiedDuration,
            m.Velocity,
            m.Note
        FROM ModifiedDurations m
        JOIN DistinctEnds d ON m.Start = d.Start;
        '''


    def _generate_add_pitch_column_command(self, texture):
        return f'''
        CREATE TABLE "{texture}_base" AS 
        SELECT 
            Start,
            End,
            Velocity,
            CAST(Note AS INTEGER) AS Note,
            CAST((Note - CAST(Note AS INTEGER)) * 4095 AS INTEGER) AS Pitch
        FROM "{texture}_end_column";
        '''
    

    def _generate_cleanup_commands(self, texture):
        temporary_tables = [
            f'"{texture}_combined"',
            f'"{texture}_max_duration"',
            'temp_table',
            f'"{texture}_end_column"'
        ]
        return [f'DROP TABLE IF EXISTS {table};' for table in temporary_tables]


    def _fetch_texture_names(self):
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        return [row[0] for row in self.cursor.fetchall()]


    def _fetch_columns(self, texture):
        exclude_columns_set = {'Start', 'Duration'}
        self.cursor.execute(f'PRAGMA table_info("{texture}")')
        return [row[1] for row in self.cursor.fetchall() if row[1] not in exclude_columns_set]


    def _generate_sql_for_duration_values(self, texture, columns_string):
        duration_values = [grid * self.scaling_factor for grid in self.grids_set]
        length_of_reps = [int(math.pow(self.period, 2) * duration) for duration in duration_values]

        table_commands = {}
        for duration_value, length_of_one_rep, repeat in zip(duration_values, length_of_reps, self.repeats):
            table_name = f"{texture}_{duration_value}"
            table_commands[table_name] = self._generate_union_all_statements(texture, columns_string, duration_value, length_of_one_rep, repeat)
        
        return table_commands


    def _generate_sql_commands(self):
        sql_commands = []

        # Fetch texture names and columns once and store
        texture_names = self._fetch_texture_names()
        texture_columns = {texture: self._fetch_columns(texture) for texture in texture_names}

        for texture in texture_names:
            columns_string = ', '.join([f'"{col}"' for col in texture_columns[texture]])
            
            table_commands = self._generate_sql_for_duration_values(texture, columns_string)
            for table_name, union_statements in table_commands.items():
                sql_commands.append(f'CREATE TABLE "{table_name}" AS {union_statements};')

            # Add other SQL commands for processing
            sql_commands.extend([
                self._generate_combined_commands(texture, self.grids_set),
                self._generate_grouped_commands(texture, texture_columns[texture]),
                self._generate_max_duration_command(texture),
                self._generate_drop_duplicates_command(texture),
                self._generate_create_end_table_command(texture),
                self._generate_insert_end_data_command(texture),
                self._generate_add_pitch_column_command(texture)
            ])
            
            # Cleanup
            sql_commands.extend(self._generate_cleanup_commands(texture))

        return "\n".join(sql_commands)


    def process_table_data(self):
        self._convert_and_store_dataframes()
        sql_commands = self._generate_sql_commands()
        self.cursor.executescript(sql_commands)
        self.database_connection.commit()
        self.database_connection.close()


    ### SET MIDI DATA
        
    def set_track_list(self):
        track_list = []
        
        for kwarg in self.kwargs.values():
            midi_track = mido.MidiTrack()
            # midi_track.append(mido.Message('program_change', program=0))
            midi_track.name = f'{kwarg.name}'
            track_list.append(midi_track)
            
        return track_list
    
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
                        
            return messages_data
    
             
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