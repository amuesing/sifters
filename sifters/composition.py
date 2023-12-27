import collections
import datetime
import decimal
import fractions
import functools
import itertools
import math
import sqlite3

import database
import mido
import music21
import pandas
import wavetable
import matrix
from textures import *


class Composition:
    
    def __init__(self, sieve, grids_set=None):
        self.sieve = sieve

        # Get the current timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Connect to SQLite database
        self.connection = sqlite3.connect(f'data/db/.{self.__class__.__name__}_{timestamp}.db')
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()

        # Initialize attributes
        self.period = None
        self.ticks_per_beat = 480
        self.scaling_factor = 100000

        # Derive normalized binary list(s) from the given sieve.
        self.binary = self.set_binary(sieve)

        # Interpolate a dictionary which tracks the indices of pattern changes within self.binary.
        self.changes = [tupl[1] for tupl in self.get_consecutive_count()]
        
        self.percent_of_period = self.get_percent_of_period(self.changes)

        # Derive a list of metric grids based on the percent of change that each integer with self.changes represents.
        self.grids_set = grids_set if grids_set is not None else self.set_grids()

        # Calculate the number of repeats needed to achieve parity between grids.
        self.repeats = self.set_repeats()

        # Initialize instances of Database, Texture, and Wavetable classes for mediation.
        self.texture = matrix.Matrix(self)
        self.database = database.Database(self)
        # self.wavetable = wavetable.Wavetable(self)
        
        # Set up notes data and tables in the database
        self.insert_data_into_database(self.texture)
        self.set_database_tables(self.database)
            

    def set_binary(self, sieve):
        # Convert sieve to Sieve object.
        obj = music21.sieve.Sieve(sieve)
        
        # Store the period of the Sieve object.
        self.period = obj.period()
        
        # Set Z range of Sieve object to [0, LCM - 1].
        obj.setZRange(0, self.period - 1)
        
        # Convert to binary and store.
        binary = obj.segment(segmentFormat='binary')

        # Return the binary representation of sieve.
        return binary


    def get_consecutive_count(self):
        # Each tuple represents an element and its consecutive count.
        consecutive_counts = [(key, len(list(group))) for key, group in itertools.groupby(self.binary)]

        return consecutive_counts
    
    
    def get_percent_of_period(self, lst): # Inner function to compute the proportion of the period that each number in the list represents.
        return [
            (decimal.Decimal(num) / decimal.Decimal(self.period)).quantize(decimal.Decimal('0.000')) 
            for num in lst
        ]

    
    def convert_decimal_to_fraction(self, decimal_list):
        return [fractions.Fraction(decimal_num) for decimal_num in decimal_list]


    def get_unique_fractions(self, input_list):
        return list(collections.OrderedDict.fromkeys(input_list))


    def set_grids(self):
        # Convert the calculated proportions to fractions.
        grids = self.convert_decimal_to_fraction(self.percent_of_period)
        
        # Remove duplicates from each grid while keeping the original order.
        grids = self.get_unique_fractions(grids) 
        
        # Return the grids containing unique fractions representing the proportion of the period.
        return grids 
    
    
    def set_textures(self):
        # Establish a dictionary mapping texture types to their associated classes.
        texture_classes = {
            # 'heterophonic': heterophonic.Heterophonic,
            # 'homophonic': homophonic.Homophonic,
            'monophonic': monophonic.Monophonic,
            # 'nonpitched': nonpitched.NonPitched,
            # 'polyphonic': polyphonic.Polyphonic,
        }

        # Generate instances of each texture type using the source data, and store them in a dictionary.
        textures_dict = {}

        for texture_type, texture_class in texture_classes.items():
            texture_instance = texture_class(self)
            textures_dict[texture_type] = texture_instance

        return textures_dict
        
    # Function to standardize the numerators in the list of grids by transforming them to a shared denominator.
    def set_normalized_numerators(self, grids):
        # Compute the least common multiple (LCM) of all denominators in the list.
        lcm = self.get_least_common_multiple([fraction.denominator for fraction in grids])
        
        # Normalize each fraction in the list by adjusting the numerator to the LCM.
        normalized_numerators = [(lcm // fraction.denominator) * fraction.numerator for fraction in grids]
        
        # Return the normalized numerators.
        return normalized_numerators


    def get_least_common_multiple(self, nums):
        if isinstance(nums, list):
            sub_lcm = [self.get_least_common_multiple(lst) for lst in nums]

            return functools.reduce(math.lcm, sub_lcm)
        else:
            return nums


    # This function computes the repetitions required for each fraction in the grids_set to equalize them.
    def set_repeats(self):
        # Standardize the numerators in the grids_set.
        normalized_numerators = self.set_normalized_numerators(self.grids_set)
        
        # Determine the least common multiple of the normalized numerators.
        least_common_multiple = self.get_least_common_multiple(normalized_numerators)
        
        # Calculate the repetition for each fraction by dividing the LCM by the normalized numerator.
        repeats = [least_common_multiple // num for num in normalized_numerators]

        # Return the repetition counts for each fraction.
        return repeats 


    def insert_data_into_database(self, texture):
        cursor = self.cursor

        # Insert texture name into textures table
        cursor.execute("INSERT INTO textures (name) VALUES (?)", (texture.__class__.__name__,))

        # Insert notes data into notes table
        texture.notes_data.to_sql(name='notes', con=self.connection, if_exists='append', index=False)

        # Save notes data to a CSV file
        csv_filename = f'data/csv/{texture.__class__.__name__}.csv'
        texture.notes_data.to_csv(csv_filename)


    def set_database_tables(self, database):
        table_names = []

        matrix_ids = database.fetch_distinct_matrix_ids()
        columns_list = database.fetch_columns_by_table_name('notes', exclude_columns={'note_id', 'Start', 'Duration'})

        for matrix_id in matrix_ids:

            table_commands = database.generate_sql_for_duration_values(matrix_id, columns_list)

            for table_name, union_statements in table_commands.items():
                table_names.append(table_name)
                self.cursor.execute(f'CREATE TEMPORARY TABLE "{table_name}" AS {union_statements};')

        self.cursor.execute('DELETE FROM notes;')
        self.cursor.executescript(database.insert_into_notes_command(table_names))

        sql_commands = []

        for matrix_id in matrix_ids:
            sql_commands.extend([
                database.generate_notes_table_commands(matrix_id),
                database.generate_midi_messages_table_commands(matrix_id),
            ])

        combined_sql = "\n".join(sql_commands)
        self.cursor.executescript(combined_sql)
        self.connection.commit()
        

    def fetch_midi_messages_from_sql(self, matrix_id):
        query = f"SELECT * FROM messages WHERE matrix_id = {matrix_id}"
        self.database.cursor.execute(query)
        return self.database.cursor.fetchall()
    
    
    def data_to_midi_messages(self, data):
        messages = []
        midi_data_list = []
        for row in data:
            message_dict = {'Message': row['Message'], 'Note': '', 'Velocity': '', 'Time': int(row['Time'] / self.scaling_factor)}
            if row['Message'] == 'note_on' or row['Message'] == 'note_off':
                msg = mido.Message(row['Message'], note=row['Note'], velocity=row['Velocity'], time=message_dict['Time'])
                message_dict['Note'] = row['Note']
                message_dict['Velocity'] = row['Velocity']

            messages.append(msg)
            midi_data_list.append(message_dict)

        return messages, midi_data_list


    def write_midi(self, matrix_id=1):
        midi_track = mido.MidiTrack()
        midi_track.name = 'mono'

        # Create a new MIDI file object
        score = mido.MidiFile()

        # Set the ticks per beat resolution
        score.ticks_per_beat = self.ticks_per_beat

        # Setting BPM
        bpm = 20  # You can change this value to set a different BPM
        tempo = int(60_000_000 / bpm)
        midi_track.append(mido.MetaMessage('set_tempo', tempo=tempo))
        
        midi_track.append(mido.MetaMessage('time_signature', numerator=5, denominator=4))

        # Fetch data and convert to MIDI messages
        data = self.fetch_midi_messages_from_sql(matrix_id)
        midi_messages, midi_data_list = self.data_to_midi_messages(data)
        
        dataframe = pandas.DataFrame(midi_data_list)
        dataframe.to_csv('data/csv/.MIDI_Messages.csv', index=False)

        # Append messages to MIDI track and save MIDI file
        for message in midi_messages:
            midi_track.append(message)

        score.tracks.append(midi_track)
        score.save('data/mid/.score.mid')
        
        
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
    
    ### WHY DOES THE BELOW GIVE ME AN ERROR?
    # sieve = '(8@5|8@6)&(5@2|5@3|5@4)'
    
    sieve = '(8@0|8@1|8@2)&5@0'
    
    # custom_grids_set = [fractions.Fraction(1, 4), fractions.Fraction(1, 2), fractions.Fraction(3, 4)]
    # comp_with_custom_grids = Composition(sieve, grids_set=custom_grids_set)
    
    comp = Composition(sieve)

    # comp.write_midi()