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

        self.database_connection.row_factory = sqlite3.Row 

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
    
    
    def _generate_midi_messages_table_command(self, texture):
        return f'''
            -- [1] Create the initial MIDI messages table:
            CREATE TABLE "{texture}_midi_messages_temp" AS
            SELECT 
                *,
                'note_on' AS Message,
                CASE 
                    WHEN ROW_NUMBER() OVER (ORDER BY Start ASC) = 1 AND Start != 0 THEN ROUND(Start * {self.ticks_per_beat})
                    ELSE 0 
                END AS Time
            FROM "{texture}_base";

            -- [2.1] Create a table of rows meeting the delta condition (generating rests):
            CREATE TABLE "{texture}_midi_rests" AS
            SELECT 
                a.*
            FROM "{texture}_midi_messages_temp" AS a
            JOIN (
                SELECT 
                    Start,
                    LAG(End) OVER (ORDER BY Start ASC) AS PreviousEnd,
                    LAG(Start) OVER (ORDER BY Start ASC) AS PreviousStart
                FROM "{texture}_midi_messages_temp"
            ) AS t
            ON a.Start = t.Start
            WHERE 
                a.Start != t.PreviousEnd 
                AND a.Start != t.PreviousStart;

            -- [2.2] Update the Time column in the main table based on delta condition:
            UPDATE "{texture}_midi_messages_temp"
            SET Time = (
                SELECT COALESCE("{texture}_midi_messages_temp".Start - t.PreviousEnd, 0)
                FROM (
                    SELECT 
                        Start,
                        LAG(End) OVER (ORDER BY Start ASC) AS PreviousEnd
                    FROM "{texture}_midi_messages_temp"
                ) AS t
                WHERE 
                    "{texture}_midi_messages_temp".Start = t.Start
            )
            WHERE EXISTS (
                SELECT 1
                FROM (
                    SELECT 
                        Start,
                        LAG(End) OVER (ORDER BY Start ASC) AS PreviousEnd,
                        LAG(Start) OVER (ORDER BY Start ASC) AS PreviousStart
                    FROM "{texture}_midi_messages_temp"
                ) AS t_sub
                WHERE 
                    "{texture}_midi_messages_temp".Start = t_sub.Start 
                    AND "{texture}_midi_messages_temp".Start != t_sub.PreviousEnd
                    AND "{texture}_midi_messages_temp".Start != t_sub.PreviousStart
            );

            -- [3] Append rows for 'pitchwheel' and 'note_off' events:
            INSERT INTO "{texture}_midi_messages_temp" (Start, End, Velocity, Note, Pitch, Message, Time)
            SELECT 
                Start, End, Velocity, Note, Pitch,
                'pitchwheel' AS Message,
                0 AS Time
            FROM "{texture}_midi_messages_temp"
            WHERE Message = 'note_on' AND Pitch != 0.0;

            INSERT INTO "{texture}_midi_messages_temp" (Start, End, Velocity, Note, Pitch, Message, Time)
            SELECT 
                Start, End, Velocity, Note, Pitch,
                'note_off' AS Message,
                (End - Start) * {self.ticks_per_beat} AS Time
            FROM "{texture}_midi_messages_temp"
            WHERE Message = 'note_on';

            -- [4] Organize the MIDI messages by 'Start' time and store in a new table:
            CREATE TABLE "{texture}_midi_messages" AS
            SELECT * FROM "{texture}_midi_messages_temp"
            ORDER BY Start ASC;

            -- [5] Cleanup: Drop the temporary table to free up resources:
            DROP TABLE "{texture}_midi_messages_temp";
        '''


    def _generate_cleanup_commands(self, texture):
        temporary_tables = [
            f'"{texture}_combined"',
            f'"{texture}_max_duration"',
            f'"{texture}_end_column"'
        ]
        return [f'DROP TABLE IF EXISTS {table};' for table in temporary_tables]


    def _generate_sql_commands(self):
        sql_commands = []

        texture_names = self._fetch_texture_names()
        texture_columns = {texture: self._fetch_columns(texture) for texture in texture_names}

        for texture in texture_names:
            columns_string = ', '.join([f'"{col}"' for col in texture_columns[texture]])
            
            table_commands = self._generate_sql_for_duration_values(texture, columns_string)
            for table_name, union_statements in table_commands.items():
                sql_commands.append(f'CREATE TABLE "{table_name}" AS {union_statements};')

            sql_commands.extend([
                self._generate_combined_commands(texture, self.grids_set),
                self._generate_grouped_commands(texture, texture_columns[texture]),
                self._generate_max_duration_command(texture),
                self._generate_drop_duplicates_command(texture),
                self._generate_create_end_table_command(texture),
                self._generate_insert_end_data_command(texture),
                self._generate_add_pitch_column_command(texture),
                self._generate_midi_messages_table_command(texture),
            ])
                
            sql_commands.extend(self._generate_cleanup_commands(texture))

        return "\n".join(sql_commands)


    def process_table_data(self):
        self._convert_and_store_dataframes()
        sql_commands = self._generate_sql_commands()
        self.cursor.executescript(sql_commands)


    def bpm_to_tempo(self, bpm):
        return int(60_000_000 / bpm)
    

    def write_midi(self, table_name):
        midi_track = mido.MidiTrack()
        midi_track.name = 'mono'

        def fetch_midi_messages_from_sql():
            query = f"SELECT * FROM {table_name}"
            self.cursor.execute(query)
            return self.cursor.fetchall()

        def data_to_midi_messages(data):
            messages = []
            midi_data_list = []
            for row in data:
                message_dict = {'Message': row['Message'], 'Note': '', 'Velocity': '', 'Time': int(row['Time'] / self.scaling_factor), 'Pitch': ''}
                if row['Message'] == 'note_on' or row['Message'] == 'note_off':
                    msg = mido.Message(row['Message'], note=row['Note'], velocity=row['Velocity'], time=message_dict['Time'])
                    message_dict['Note'] = row['Note']
                    message_dict['Velocity'] = row['Velocity']
                elif row['Message'] == 'pitchwheel':
                    msg = mido.Message(row['Message'], pitch=row['Pitch'], time=message_dict['Time'])
                    message_dict['Pitch'] = row['Pitch']

                messages.append(msg)
                midi_data_list.append(message_dict)

            return messages, midi_data_list

        def save_messages_to_csv(midi_data_list, filename):
            df = pandas.DataFrame(midi_data_list)
            df.to_csv(filename, index=False)

        # Create a new MIDI file object
        score = mido.MidiFile()

        # Set the ticks per beat resolution
        score.ticks_per_beat = self.ticks_per_beat

        # Setting BPM
        bpm = 33  # You can change this value to set a different BPM
        tempo = self.bpm_to_tempo(bpm)
        midi_track.append(mido.MetaMessage('set_tempo', tempo=tempo))
        
        midi_track.append(mido.MetaMessage('time_signature', numerator=5, denominator=4))

        # Fetch data and convert to MIDI messages
        data = fetch_midi_messages_from_sql()
        midi_messages, midi_data_list = data_to_midi_messages(data)

        # Save to CSV
        save_messages_to_csv(midi_data_list, 'data/csv/.MIDI_Messages.csv')

        # Append messages to MIDI track and save MIDI file
        for message in midi_messages:
            midi_track.append(message)

        score.tracks.append(midi_track)
        score.save('data/mid/score.mid')
        
        
if __name__ == '__main__':

    # sieve = '''
    #         (((8@0|8@1|8@7)&(5@1|5@3))|
    #         ((8@0|8@1|8@2)&5@0)|
    #         ((8@5|8@6)&(5@2|5@3|5@4))|
    #         (8@6&5@1)|
    #         (8@3)|
    #         (8@4)|
    #         (8@1&5@2))
    #         '''

    sieve = '''
        ((8@0|8@1|8@7)&(5@1|5@3))
        '''
        
    comp = Composition(sieve)
    
    comp.process_table_data()

    comp.write_midi('monophonic_midi_messages')

    comp.database_connection.commit()
    comp.database_connection.close()