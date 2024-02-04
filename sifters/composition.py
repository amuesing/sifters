import collections
import decimal
import fractions
import functools
import itertools
import math

import database
import matplotlib.pyplot
import mido
import music21
import numpy
import pandas
import scipy.io.wavfile
import wavetable


class Composition:
    
    
    def __init__(self, sieve, grids_set=None, normalized_grids=False):
        self.ticks_per_beat = 480
        self.scaling_factor = 100000
        
        self.sieve = sieve
        self.period = None
        self.binary = self.set_binary(sieve)
        self.normalized_grids = normalized_grids
        
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
    
    
    # Inner function to compute the proportion of the period that each number in the list represents.
    def get_percent_of_period(self, lst): 
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
        
        # Grid fractions are sorted in numerical order so highest frequency last when converting to FM.
        sorted_grids = sorted(grids)
        
        # Return the grids containing unique fractions representing the proportion of the period.
        return sorted_grids
    
        
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
        
        
if __name__ == '__main__':
    
    
    def create_dataframe(notes_data):
        columns = ['Start', 'Velocity', 'Note', 'Duration', 'GridID']
        dataframe = pandas.DataFrame(notes_data, columns=columns)
        dataframe = dataframe.sort_values(by='Start').drop_duplicates().reset_index(drop=True)
        dataframe = dataframe.apply(pandas.to_numeric, errors='ignore')
        return dataframe
    
    
    def generate_notes_data(comp):
        notes_data = []
        indice_list = []
        velocity = 64
        texture_id = 1
        
        steps = comp.get_successive_diff(comp.indices)
        normalized_matrix = comp.generate_pitchclass_matrix(comp.indices)
        matrix_represented_by_size = comp.represent_matrix_by_size(normalized_matrix)
        matrix_represented_by_size = comp.convert_matrix_to_dataframe(matrix_represented_by_size)
        sieve_adjusted_by_step = comp.indices[0] + normalized_matrix
        sieve_adjusted_by_step = comp.convert_matrix_to_dataframe(sieve_adjusted_by_step)
        print(f'Number of unique matrix elements: {comp.convert_matrix_to_dataframe(normalized_matrix).stack().nunique()}')
        
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
        notes_data = create_dataframe(notes_data)
        notes_data.to_csv('data/csv/Notes_Data.csv', index=False)
        return notes_data
    
    
    def set_database_tables(db, notes_data):
        table_names = []
        sql_commands = []
        
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
        
        grid_ids = db.select_distinct_grids()
        
        for grid_id in grid_ids:
            sql_commands.append(db.generate_max_duration_commands(grid_id)),
            sql_commands.append(db.preprocess_max_duration(grid_id)),
            sql_commands.append(db.generate_end_column_command(grid_id)),
            sql_commands.append(db.insert_end_column_data(grid_id)),
            sql_commands.append(db.generate_message_column_command(grid_id)),
            sql_commands.append(db.insert_message_column_data(grid_id)),
            sql_commands.append(db.create_temporary_midi_messages_table(grid_id)),
            sql_commands.append(db.append_note_off_message(grid_id)),
            sql_commands.append(db.order_midi_messages_by_start(grid_id)),
            sql_commands.append(db.insert_into_messages_table(grid_id)),
        
        combined_sql = "\n".join(sql_commands)
        db.cursor.executescript(combined_sql)
        db.connection.commit()
        
        
    def fetch_midi_messages_for_grid_id(grid_id):
        query = f"SELECT * FROM messages WHERE GridID = {grid_id}"
        db.cursor.execute(query)
        return db.cursor.fetchall()

    
    def data_to_midi_messages(data, scaling_factor):
        messages = []
        midi_data_list = []
        for row in data:
            # Increase the time value of the MIDI message by dividing the scaling_factor by 10.
            message_dict = {'Message': row['Message'], 'Note': '', 'Velocity': '', 'Time': int(row['Time'] / (scaling_factor / 10))}
            if row['Message'] == 'note_on' or row['Message'] == 'note_off':
                msg = mido.Message(row['Message'], note=row['Note'], velocity=row['Velocity'], time=message_dict['Time'])
                message_dict['Note'] = row['Note']
                message_dict['Velocity'] = row['Velocity']

            messages.append(msg)
            midi_data_list.append(message_dict)

        return messages, midi_data_list
    
    
    def visualize_fm_synthesis(self, modulating_frequencies, enveloped_carrier, modulator_envelopes, synthesis_type='linear'):
        for i, modulating_frequency in enumerate(modulating_frequencies):
            modulating_wave = self.generate_sine_wave(frequency=modulating_frequency)
            
            # Original FM waveform without ADSR envelope
            fm_wave = self.perform_fm_synthesis(enveloped_carrier, modulating_wave, synthesis_type=synthesis_type)

            enveloped_modulator = modulating_wave * modulator_envelopes[i]
            fm_wave_with_adsr = self.perform_fm_synthesis(enveloped_carrier, enveloped_modulator, synthesis_type=synthesis_type)

            # Superimposed plot for each grid
            matplotlib.pyplot.plot(fm_wave, label=f'Original FM Wave ({self.grids_set[i]} fraction)')
            matplotlib.pyplot.plot(fm_wave_with_adsr, label=f'FM Wave with ADSR ({self.grids_set[i]} fraction)')

        matplotlib.pyplot.title(f'FM Synthesis with Unique ADSR Envelopes ({synthesis_type.capitalize()} Synthesis)')
        matplotlib.pyplot.xlabel('Sample')
        matplotlib.pyplot.ylabel('Amplitude')
        matplotlib.pyplot.legend()
        matplotlib.pyplot.show()



    def save_fm_waveforms(self, modulating_frequencies, enveloped_carrier, modulator_envelopes, synthesis_type='linear'):
        for i, modulating_frequency in enumerate(modulating_frequencies):
            modulating_wave = self.generate_sine_wave(frequency=modulating_frequency)

            enveloped_modulator = modulating_wave * modulator_envelopes[i]
            fm_wave_with_adsr = self.perform_fm_synthesis(enveloped_carrier, enveloped_modulator, synthesis_type=synthesis_type)

            scipy.io.wavfile.write(f'data/wav/fm_wave_{i + 1}_{synthesis_type}.wav', self.sample_rate, self.normalize_waveform(fm_wave_with_adsr))

        print(f"{synthesis_type.capitalize()} WAV files saved successfully.")



    def write_midi(comp, grid_id):
        midi_track = mido.MidiTrack()
        midi_track.name = f'grid_{grid_id}'

        # Create a new MIDI file object
        score = mido.MidiFile()

        # Set the ticks per beat resolution
        score.ticks_per_beat = comp.ticks_per_beat

        # Setting BPM
        bpm = 60  # You can change this value to set a different BPM
        tempo = int(60_000_000 / bpm)
        midi_track.append(mido.MetaMessage('set_tempo', tempo=tempo))
        # midi_track.append(mido.MetaMessage('time_signature', numerator=5, denominator=4))

        # Fetch data for the specific GridID and convert to MIDI messages
        data = fetch_midi_messages_for_grid_id(grid_id)
        midi_messages, midi_data_list = data_to_midi_messages(data, comp.scaling_factor)
        dataframe = pandas.DataFrame(midi_data_list)
        dataframe.to_csv(f'data/csv/MIDI_Messages_GridID_{grid_id}.csv', index=False)

        # Append messages to MIDI track and save MIDI file
        for message in midi_messages:
            midi_track.append(message)

        score.tracks.append(midi_track)
        score.save(f'data/mid/Grid_{grid_id}.mid')


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
        
    ### WHY DOES THE BELOW GIVE ME AN ERROR?
    # sieve = '(8@5|8@6)&(5@2|5@3|5@4)'
    
    ### WHY DOES THE BELOW GIVE ME A STRANGE TUNING FILE
    # siv = '(8@0|8@1|8@2)&5@0|(8@1&5@2)'
    
    comp = Composition(sieve)
    notes_data = generate_notes_data(comp)
    
    db = database.Database(comp)
    db.clear_database()
    set_database_tables(db, notes_data)
    grid_ids = db.select_distinct_grids()
    
    ### ENVELOPES AND MODULATION INDEX SEEM TO MAKE THE MOST AUDITORY DIFFERENCE.
    ### HOW TO ASSIGN ENVELOPES VALUES IN A PROGRAMATIC WAY?
    ### HOW TO ASSIGN MODULATION INDEX IN A PROGRAMATIC WAY?
    synth = wavetable.Wavetable(comp)
    synthesis_type = 'exponential'
    frequency_multiplier = 16
    
    carrier_wave = synth.generate_sine_wave(frequency=synth.reference_frequency * frequency_multiplier)
    carrier_envelope = synth.generate_adsr_envelope(attack_time=0.1, decay_time=0.4, sustain_level=0.8, release_time=0.1)
    enveloped_carrier = carrier_wave * carrier_envelope
    
    modulating_frequencies = [grid_fraction * synth.reference_frequency * frequency_multiplier for grid_fraction in comp.grids_set]
    modulator_envelopes = [
        synth.generate_adsr_envelope(
            attack_time=0.1 + 0.05 * i,
            decay_time=0.4 - 0.05 * i,
            sustain_level=0.55 + 0.05 * i,
            release_time=0.2,
            length=synth.num_samples
        )
        for i in range(len(comp.grids_set))
    ]

    # Visualize and save FM synthesis results
    synth.visualize_fm_synthesis(modulating_frequencies, enveloped_carrier, modulator_envelopes,
                                synthesis_type=synthesis_type)
    synth.save_fm_waveforms(modulating_frequencies, enveloped_carrier, modulator_envelopes,
                            synthesis_type=synthesis_type)

    for grid_id in grid_ids:
        write_midi(comp, grid_id)
