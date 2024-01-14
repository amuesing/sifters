import collections
import decimal
import fractions
import functools
import itertools
import math

import database
import mido
import music21
import numpy
import pandas
from generators import *


class Composition:
    
    
    def __init__(self, sieve, grids_set=None):
        self.ticks_per_beat = 480
        self.scaling_factor = 100000
        
        self.sieve = sieve
        self.period = None
        self.binary = self.set_binary(sieve)
        
        # Interpolate a dictionary which tracks the indices of pattern changes within self.binary.
        self.changes = [tupl[1] for tupl in self.get_consecutive_count()]
        
        self.percent_of_period = self.get_percent_of_period(self.changes)

        # Derive a list of metric grids based on the percent of change that each integer with self.changes represents.
        self.grids_set = grids_set if grids_set is not None else self.set_grids()

        # Calculate the number of repeats needed to achieve parity between grids.
        self.repeats = self.set_repeats()
        self.indices = numpy.nonzero(self.binary)[0]
        self.factors = [i for i in range(1, self.period + 1) if self.period % i == 0]
        
        
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
    
    
    def get_successive_diff(self, integers):
        return [0] + [integers[i+1] - integers[i] for i in range(len(integers)-1)]
    
        
    
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
    
    
    def represent_by_size(self, steps):
        sorted_list = sorted(steps)
        sorted_set = set(sorted_list)

        # Create a dictionary to store the index for each value
        index_mapping = {value: rank for rank, value in enumerate(sorted_set)}

        # Map each element in the original list to its index in the sorted set
        steps = [index_mapping[value] for value in steps]
        
        return steps

    
    def unflatten_list(self, flat_list, original_matrix):
        # Assuming original_matrix is a list of lists
        rows, cols = len(original_matrix), len(original_matrix[0])

        # Reshape the flat_list back to the original Sieve shape
        reshaped_matrix = [flat_list[i * cols:(i + 1) * cols] for i in range(rows)]

        return reshaped_matrix
    
    
    def generate_pitchclass_matrix(self, intervals):
        next_interval = intervals[1:]
        row = [next_interval[i] - intervals[0] for i in range(len(intervals) - 1)]
        
        matrix = [
            [
                (0 - row[i]) % (self.period - 1)
            ] 
            for i in range(len(intervals) - 1)
        ]

        row.insert(0, 0)
        matrix.insert(0, [0])
        
        matrix = [
            [
                (matrix[i][0] + row[j]) % (self.period - 1)
                for j in range(len(matrix))
            ]
            for i in range(len(matrix))
        ]

        return matrix
    
    
    def represent_matrix_by_size(self, matrix):
        flattened_matrix = [value for lst in matrix for value in lst]
        
        sized_matrix = self.represent_by_size(flattened_matrix)

        # Unflatten the sized list back to the original Sieve structure
        matrix = self.unflatten_list(sized_matrix, matrix)
        
        return matrix
    
    
    def convert_matrix_to_dataframe(self, matrix):
        # Convert the unflattened Sieve to a DataFrame
        matrix = pandas.DataFrame(matrix,
                                    index=[f'P{m[0]}' for m in matrix], 
                                    columns=[f'I{i}' for i in matrix[0]])
        
        return matrix
    
    
    def generate_note_pool_from_matrix(self, matrix, num_of_positions, steps):
        pool = []
        current_index = 0
        retrograde = False
        steps_cycle = itertools.cycle(steps)

        for _ in range(num_of_positions):
            step = next(steps_cycle)

            wrapped_index = (current_index + abs(step)) % len(self.indices)
            wrap_count = (abs(step) + current_index) // len(self.indices)

            if wrap_count % 2 == 1:
                retrograde = not retrograde

            if step >= 0:
                if retrograde:
                    pool.append(matrix.iloc[wrapped_index][::-1].tolist())
                else:
                    pool.append(matrix.iloc[wrapped_index].tolist())
            if step < 0:
                if retrograde:
                    pool.append(matrix.iloc[:, wrapped_index][::-1].tolist())
                else:
                    pool.append(matrix.iloc[:, wrapped_index].tolist())

            current_index = wrapped_index
        

        return pool
    
    
    def create_tuning_file(self, floats_list):
        title = f'Base {self.period} Tuning'
        description = 'Tuning based on the periodicity of a logical sieve, selecting for degrees that coorespond to non-zero sieve elements.'
        file_name = 'data/scl/tuning.scl'
        # Construct the file_content
        file_content = f'''! {title}
!
{description}
{len(floats_list) + 1}
!
'''

        # Add floats to the content
        file_content += '\n'.join(map(str, floats_list))
        
        # Add '2/1' on its own line
        file_content += '\n2/1'

        # Open the file in write mode ('w')
        with open(file_name, 'w') as file:
            # Write content to the file
            file.write(file_content)
        
    
    def select_scalar_segments(self, indice_list):
        cents = []

        for i in range(self.period):
            cent_value = (1200 / self.period) * i
            cent_value = round(cent_value, 6)
            cents.append(cent_value)

        # Select cents at specific indices
        self.selected_cents_implied_zero = [cents[index - indice_list[0]] for index in indice_list][1:]

        # Create tuning file using the selected cents
        self.create_tuning_file(self.selected_cents_implied_zero)

        # Return the original list of cents
        return cents
    
    
    def create_dataframe(self, notes_data):
        columns = ['Start', 'Velocity', 'Note', 'Duration', 'GridID']
        dataframe = pandas.DataFrame(notes_data, columns=columns)
        dataframe = dataframe.sort_values(by='Start').drop_duplicates().reset_index(drop=True)
        dataframe = dataframe.apply(pandas.to_numeric, errors='ignore')
        return dataframe

    
    def fetch_midi_messages_from_sql(self):
        query = "SELECT * FROM messages"
        db.cursor.execute(query)
        return db.cursor.fetchall()

    
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


    def write_midi(self):
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
        data = self.fetch_midi_messages_from_sql()
        midi_messages, midi_data_list = self.data_to_midi_messages(data)
        
        dataframe = pandas.DataFrame(midi_data_list)
        dataframe.to_csv('data/csv/.MIDI_Messages.csv', index=False)

        # Append messages to MIDI track and save MIDI file
        for message in midi_messages:
            midi_track.append(message)

        score.tracks.append(midi_track)
        score.save('data/mid/score.mid')
        
        
if __name__ == '__main__':
    
    
    def generate_notes_data(comp):
        notes_data = []
        indice_list = []
        velocity = 64
        texture_id = 1
        
        steps = comp.get_successive_diff(comp.indices)
        normalized_Sieve = comp.generate_pitchclass_matrix(comp.indices)
        matrix_represented_by_size = comp.represent_matrix_by_size(normalized_Sieve)
        matrix_represented_by_size = comp.convert_matrix_to_dataframe(matrix_represented_by_size)
        sieve_adjusted_by_step = comp.indices[0] + normalized_Sieve
        sieve_adjusted_by_step = comp.convert_matrix_to_dataframe(sieve_adjusted_by_step)
        
        # For each factor, create exactly the number of notes required for each texture to achieve parity
        for factor_index in range(len(comp.factors)):
            num_of_events = (len(comp.indices) * comp.factors[factor_index])
            num_of_positions = num_of_events // len(steps)
            pool = comp.generate_note_pool_from_matrix(matrix_represented_by_size, num_of_positions, steps)
            adjusted_pool = comp.generate_note_pool_from_matrix(sieve_adjusted_by_step, num_of_positions, steps)
            flattened_pool = [num for list in pool for num in list]
            indice_list = [num for list in adjusted_pool for num in list]

            note_pool = itertools.cycle(flattened_pool)
            tiled_pattern = numpy.tile(comp.binary, comp.factors[factor_index])
            tiled_indices = numpy.nonzero(tiled_pattern)[0]

            duration = comp.period // comp.factors[factor_index]
            
            for index in tiled_indices:
                start = index * duration
                notes_data.append((start, velocity, next(note_pool), duration, texture_id))
        
        comp.select_scalar_segments(list(set(indice_list)))
        notes_data = comp.create_dataframe(notes_data)
        notes_data.to_csv('data/csv/.Notes_Data.csv', index=False)
        return notes_data
    
    
    def generate_notes_table_commands(db):
        commands = []
        commands.append(db.generate_max_duration_command())
        commands.append(db.preprocess_max_duration())
        commands.append(db.generate_end_column_command())
        commands.append(db.insert_end_column_data())
        commands.append(db.generate_message_column_command())
        commands.append(db.insert_message_column_data())

        return '\n'.join(commands)
    
    
    def generate_midi_messages_table_commands(db):
        command = []
        command.append(db.create_temporary_midi_messages_table())
        command.append(db.append_note_off_message())
        command.append(db.order_midi_messages_by_start())
        command.append(db.insert_into_messages_table())

        return '\n'.join(command)
    
    
    def set_database_tables(db, notes_data):
        table_names = []
        
        db.create_grids_table()
        db.create_notes_table()
        db.create_messages_table()
        db.insert_dataframe_into_database('notes', notes_data)

        columns_list = db.fetch_columns_by_table_name('notes', exclude_columns={'Start', 'Duration', 'NoteID', 'GridID'})

        table_commands = db.generate_duration_commands(columns_list)

        for table_name, union_statements in table_commands.items():
            table_names.append(table_name)
            db.cursor.execute(f'CREATE TEMPORARY TABLE "{table_name}" AS {union_statements};')

        db.cursor.execute('DELETE FROM notes;')
        db.cursor.executescript(db.insert_into_notes_command(table_names))

        sql_commands = [
                generate_notes_table_commands(db),
                generate_midi_messages_table_commands(db),
                ]
        
        combined_sql = "\n".join(sql_commands)
        db.cursor.executescript(combined_sql)
        db.connection.commit()


    sieve = '''
            (((8@0|8@1|8@7)&(5@1|5@3))|
            ((8@0|8@1|8@2)&5@0)|
            ((8@5|8@6)&(5@2|5@3|5@4))|
            (8@6&5@1)|
            (8@3)|
            (8@4)|
            (8@1&5@2))
            '''
    
    # sieve = '''
    #         (8@1&5@2)
    #         '''
    
    ### THIS SHOULD BE A TABLE BASED ON THE DIFFERENT GRIDS,
    ### THEN EACH GRID SHOULD BE TRACKED WITHIN THE NOTES TABLE
    
    ### WHY DOES THE BELOW GIVE ME AN ERROR?
    # sieve = '(8@5|8@6)&(5@2|5@3|5@4)'
    
    ### WHY DOES THE BELOW GIVE ME A STRANGE TUNING FILE
    # siv = '(8@0|8@1|8@2)&5@0|(8@1&5@2)'
    
    comp = Composition(sieve)
    notes_data = generate_notes_data(comp)
    db = database.Database(comp)
    set_database_tables(db, notes_data)
    comp.write_midi()