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
from textures import (heterophonic, homophonic, monophonic, nonpitched,
                      polyphonic)


class Composition:
    
    def __init__(self, sieve):

        # Assign sieves argument to self.
        self.sieve = sieve

        # Get the current timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Connect to SQLite database
        self.connection = sqlite3.connect(f'data/db/.{self.__class__.__name__}_{timestamp}.db')

        self.connection.row_factory = sqlite3.Row

        self.cursor = self.connection.cursor()

        # Initialize a period variable which will be assigned to an integer within the set_binary method.
        self.period = None

        self.ticks_per_beat = 480

        self.scaling_factor = 100000

        # Derive normalized binary list(s) from the given sieve.
        self.binary = self.set_binary(sieve)

        # Interpolate a dictionary which tracks the indicies of pattern changes within self.binary.
        self.changes = [tupl[1] for tupl in self.get_consecutive_count()]

        # Derive self-similar lists of integers based on the self.changes attribute.
        self.form = [[num] * len(self.changes) for num in self.changes]

        # Derive a list of metric grids based on the percent of change that each integer with self.changes represents.
        self.grids_set = self.set_grids()

        # Calculate the number of repeats needed to achieve parity between grids.
        self.repeats = self.set_repeats()

        # Initialize an instance of the Utility class to call helper methods from.
        self.database = database.Database(self)

        # Generate contrapuntal textures derived from the binary, grids_set, and repeats attributes.
        self.initialize_texture_objects()

        self.generate_sql_commands()
            

    def set_binary(self, sieve):
        obj = music21.sieve.Sieve(sieve)  # Convert sieve to Sieve object.
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
    

    def _get_least_common_multiple(self, nums):

        if isinstance(nums, list):
            sub_lcm = [self._get_least_common_multiple(lst) for lst in nums]

            return functools.reduce(math.lcm, sub_lcm)
        
        else:
            return nums
    
    
    # Inner function to standardize the numerators in the list of grids by transforming them to a shared denominator.
    def _set_normalized_numerators(self, grids):
        # Compute the least common multiple (LCM) of all denominators in the list.
        lcm = self._get_least_common_multiple([fraction.denominator for fraction in grids])
        
        # Normalize each fraction in the list by adjusting the numerator to the LCM.
        normalized_numerators = [(lcm // fraction.denominator) * fraction.numerator for fraction in grids]
        
        # Return the normalized numerators.
        return normalized_numerators


    # This function computes the repetitions required for each fraction in the grids_set to equalize them.
    def set_repeats(self):
        # Standardize the numerators in the grids_set.
        normalized_numerators = self._set_normalized_numerators(self.grids_set)
        
        # Determine the least common multiple of the normalized numerators.
        least_common_multiple = self._get_least_common_multiple(normalized_numerators)

        # Calculate the repetition for each fraction by dividing the LCM by the normalized numerator.
        repeats = [least_common_multiple // num for num in normalized_numerators]

        # Return the repetition counts for each fraction.
        return repeats


    def initialize_texture_objects(self):
        # List of texture classes.
        texture_classes = [
            heterophonic.Heterophonic,
            homophonic.Homophonic,
            monophonic.Monophonic,
            nonpitched.NonPitched,
            polyphonic.Polyphonic,
        ]
        
        # Simply initialize each texture object. No need to store them.
        for TextureClass in texture_classes:
            TextureClass(self)  # Initialize with the Composition instance as a mediator


    def generate_sql_commands(self):
        sql_commands = []
        exclude_columns_set = {'Start', 'Duration'}
        texture_names = self.database.fetch_texture_names()
        texture_columns = {texture: self.database.fetch_columns(texture, exclude_columns_set) for texture in texture_names}

        for texture_name in texture_names:
            table_names = []
            columns_string = ', '.join([f'"{col}"' for col in texture_columns[texture_name]])
            texture_id = self.database.find_first_texture_id(texture_name)
            
            table_commands = self.database.generate_sql_for_duration_values(texture_name, columns_string)
            for table_name, union_statements in table_commands.items():
                table_names.append(table_name)
                self.cursor.execute(f'CREATE TABLE "{table_name}" AS {union_statements};')

            sql_commands.extend([
                self.database.insert_texture(texture_id, texture_name),
                self.database.insert_into_notes_command(table_names),  # Insert records from the texture into the notes table
                # self.database.generate_combined_commands(texture, self.grids_set),
                # self.database.generate_grouped_commands(texture, texture_columns[texture]),
                # self.database.generate_max_duration_command(texture),
                # self.database.generate_drop_duplicates_command(texture),
                # self.database.generate_create_end_table_command(texture),
                # self.database.generate_insert_end_data_command(texture),
                # self.database.generate_add_pitch_column_command(texture),
                # self.database.generate_midi_messages_table_command(texture),
            ])
                
            sql_commands.extend(self.database.generate_cleanup_commands(texture_name))

        sql_commands = "\n".join(sql_commands)
        self.cursor.executescript(sql_commands)


    def write_midi(self, table_name):
        midi_track = mido.MidiTrack()
        midi_track.name = 'mono'

        def bpm_to_tempo(bpm):
            return int(60_000_000 / bpm)

        def fetch_midi_messages_from_sql():
            query = f"SELECT * FROM {table_name}"
            self.database.cursor.execute(query)
            return self.database.cursor.fetchall()

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
        tempo = bpm_to_tempo(bpm)
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
    
    comp.connection.commit()

    # comp.write_midi('Monophonic_midi_messages')

    comp.connection.close()