import music21
import pretty_midi
import fractions
import itertools
import functools
import decimal
import pandas
import numpy
import math

class Composition:
    # Return a serial matrix given a list of integers.
    def generate_pitchclass_matrix(intervals):
        next_interval = intervals[1:] # List of intervals, starting from the second value.
        row = [0] + [next_interval[i] - intervals[0] for i, _ in enumerate(intervals[:-1])] # Normalize tone row.
        matrix = [[abs(decimal.Decimal(str(note)) - decimal.Decimal('12')) % decimal.Decimal('12')] for note in row] # Generate matrix rows.
        matrix = [r * len(intervals) for r in matrix] # Generate matrix columns.
        matrix = [[(matrix[i][j] + decimal.Decimal(str(row[j]))) % decimal.Decimal('12') for j, _ in enumerate(range(len(row)))] for i in range(len(row))] # Update vectors with correct value.
        matrix = pandas.DataFrame(matrix, index=[f'P{m[0]}' for m in matrix], columns=[f'I{i}' for i in matrix[0]]).astype(float) # Label rows and collumns.
        inverted_matrix = ([matrix.iloc[:, i].values.tolist() for i, _ in enumerate(matrix)])
        return matrix
    
    # Make all these 'with_start' method work as single methods
    # Group the notes_data dataframe by the 'Start' collumn.
    @staticmethod
    def group_by_start(dataframe):
        grouped_velocity = dataframe.groupby('Start')['Velocity'].apply(lambda x: sorted(set(x)))
        grouped_midi = dataframe.groupby('Start')['MIDI'].apply(lambda x: sorted(set(x)))
        # grouped_pitch = dataframe.groupby('Start')['Pitch'].apply(lambda x: sorted(set(x)))
        grouped_end = dataframe.groupby('Start')['End'].apply(lambda x: sorted(set(x)))
        result = pandas.concat([grouped_velocity, grouped_midi, grouped_end], axis=1).reset_index()
        result = result[['Velocity', 'MIDI', 'Start', 'End']]
        return result
    
    @staticmethod
    def group_by_start_with_pitch(dataframe):
        grouped_velocity = dataframe.groupby('Start')['Velocity'].apply(lambda x: sorted(set(x)))
        grouped_midi = dataframe.groupby('Start')['MIDI'].apply(lambda x: sorted(set(x)))
        grouped_pitch = dataframe.groupby('Start')['Pitch'].apply(lambda x: sorted(set(x)))
        grouped_end = dataframe.groupby('Start')['End'].apply(lambda x: sorted(set(x)))
        result = pandas.concat([grouped_velocity, grouped_midi, grouped_pitch, grouped_end], axis=1).reset_index()
        result = result[['Velocity', 'MIDI', 'Pitch', 'Start', 'End']]
        return result
    
    @staticmethod
    def get_lowest_midi(dataframe):
        dataframe['MIDI'] = dataframe['MIDI'].apply(lambda x: min(x) if x else None)
        dataframe = dataframe.dropna(subset=['MIDI'])
        return dataframe[['Velocity', 'MIDI', 'Start', 'End']]
    
    @staticmethod
    def get_lowest_midi_with_pitch(dataframe):
        dataframe['MIDI'] = dataframe['MIDI'].apply(lambda x: min(x) if x else None)
        dataframe = dataframe.dropna(subset=['MIDI'])
        return dataframe[['Velocity', 'MIDI', 'Pitch', 'Start', 'End']]
    
    def check_and_close_intervals(self, dataframe):
        for i in range(len(dataframe['MIDI']) - 1):
            if abs(dataframe['MIDI'][i] - dataframe['MIDI'][i + 1]) > 6: 
                dataframe = self.close_intervals(dataframe)
                # dataframe = self.adjust_midi_range(dataframe)
                return self.check_and_close_intervals(dataframe)
        return dataframe
    
    @staticmethod
    def close_intervals(dataframe):
        updated_df = dataframe.copy()
        for i, midi in enumerate(updated_df["MIDI"][:-1]):
            next_midi = updated_df["MIDI"][i + 1]
            if midi - next_midi > 6:
                updated_df.at[i + 1, "MIDI"] = round(next_midi + 12, 3)
            elif midi - next_midi < -6:
                updated_df.at[i + 1, "MIDI"] = round(next_midi - 12, 3)
        return updated_df
    
    # How to make it so that this adjustment hinges on the close_intervals so that if the range is greater than 6 it will increase, unless within a certain range.
    @staticmethod
    def adjust_midi_range(dataframe):
        # Define the lambda function to adjust values outside the range [0, 127]
        adjust_value = lambda x: x - 12 if x > 108 else (x + 12 if x < 24 else x)
        # Apply the lambda function repeatedly until all values satisfy the condition
        while dataframe['MIDI'].apply(lambda x: x < 24 or x > 108).any():
            dataframe['MIDI'] = dataframe['MIDI'].apply(adjust_value)
        return dataframe
    
    @staticmethod
    def combine_consecutive_midi_values(dataframe):
        result = []
        current_velocity = None
        current_midi = None
        current_start = None
        current_end = None
        for _, row in dataframe.iterrows():
            if current_midi == row['MIDI']:
                current_end = row['End']
            else:
                if current_midi is not None:
                    result.append([current_velocity, current_midi, current_start, current_end])
                current_velocity = row['Velocity']
                current_midi = row['MIDI']
                current_start = row['Start']
                current_end = row['End']
        result.append([current_velocity, current_midi, current_start, current_end,])
        return pandas.DataFrame(result, columns=['Velocity', 'MIDI', 'Start', 'End'])
    
    @staticmethod
    def combine_consecutive_midi_values_with_pitch(dataframe):
        result = []
        current_velocity = None
        current_midi = None
        current_pitch = None
        current_start = None
        current_end = None
        for _, row in dataframe.iterrows():
            if current_midi == row['MIDI']:
                current_end = row['End']
            else:
                if current_midi is not None:
                    result.append([current_velocity, current_midi, current_pitch, current_start, current_end])
                current_velocity = row['Velocity']
                current_midi = row['MIDI']
                current_pitch = row['Pitch']
                current_start = row['Start']
                current_end = row['End']
        result.append([current_velocity, current_midi, current_pitch, current_start, current_end,])
        return pandas.DataFrame(result, columns=['Velocity', 'MIDI', 'Pitch', 'Start', 'End'])
    
    @staticmethod
    def convert_lists_to_scalars(dataframe):
        for col in dataframe.columns:
            if dataframe[col].dtype == object:
                dataframe[col] = dataframe[col].apply(lambda x: x[0] if isinstance(x, (list, tuple)) else x)
        return dataframe
    
class Score(Composition):
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.normalized_numerators = numpy.array([self.normalize_numerator(arg, self.get_multiplier(arg)) for arg in self.kwargs.values()])
        self.multipliers = list(self.kwargs.values())[-1].get_least_common_multiple(self.normalized_numerators) // self.normalized_numerators
        self.set_instrumentation()
        self.normalize_periodicity()
        
    @staticmethod
    def get_multiplier(arg):
        lcd = functools.reduce(math.lcm, (fraction.denominator for fraction in arg.grid_history))
        return [lcd // fraction.denominator for fraction in arg.grid_history][arg.part_id-1]
    
    @staticmethod
    def normalize_numerator(arg, mult):
        return arg.grid_history[arg.part_id-1].numerator * mult
    
    def set_instrumentation(self):
        instruments_list = []
        for kwarg in self.kwargs.values():
            instruments_list.append(pretty_midi.Instrument(program=0, name=f'{kwarg.name}'))
        self.instrumentation = instruments_list
        
    def normalize_periodicity(self):
        normalized_parts_data = [] # Create an empty list to store the normalized notes_data.
        for arg, multiplier in zip(self.kwargs.values(), self.multipliers): # Iterate over the kwargs.values() and self.multipliers.
            duplicates = [arg.notes_data.copy()] # Create a list to store the original notes_data and the copies that will be normalized.
            length_of_one_rep = math.pow(arg.period, 2) # Calculate the length of one repetition.
            for i in range(multiplier): # Iterate over the range of multipliers to create copies of notes_data.
                dataframe_copy = arg.notes_data.copy() # Create a copy of notes_data.
                dataframe_copy['Start'] = round(dataframe_copy['Start'] + (length_of_one_rep * arg.grid) * i, 6) # Adjust the Start column of the copy based on the length of one repitition and grid value.
                dataframe_copy['End'] = round(dataframe_copy['End'] + (length_of_one_rep * arg.grid) * i, 6) # Adjust the End column of the copy based on the length of one repitition and grid value.
                duplicates.append(dataframe_copy) # Append the copy to the duplicates list.
            result = pandas.concat(duplicates) # Concatenate the duplicates list into a single dataframe.
            result = result.drop_duplicates() # Remove duplicate rows from the concatenated dataframe.
            normalized_parts_data.append(result) # Append the normalized dataframe to the normalized_parts_data list.
        self.normalized_parts_data = normalized_parts_data # Store the normalized_parts_data in self.normalized_parts_data.
        
    def write_score(self):
        score = pretty_midi.PrettyMIDI()
        # Write method to determine TimeSignature
        score.time_signature_changes.append(pretty_midi.TimeSignature(5, 4, 0))
        score.resolution = score.resolution * 2
        note_objects = [self.csv_to_note_object(part) for part in self.normalized_parts_data]
        bend_objects = [self.csv_to_bend_object(part) for part in self.normalized_parts_data]
        for i, _ in enumerate(note_objects):
            self.instrumentation[i].notes = note_objects[i]
            self.instrumentation[i].pitch_bends = bend_objects[i]
            score.instruments.append(self.instrumentation[i])
        # Not working for combined parts because midi goes below 0, write a function to ensure that part is within a certain range of midi notes
        score.write(f'sifters/.score.mid')
        # self.normalized_parts_data[0].to_csv('norm df')
        
    @staticmethod
    def csv_to_note_object(dataframe):
        dataframe.to_csv('note_obj', index=False)
        # Use a list comprehension to generate a list of pretty_midi.Note objects from the input dataframe
        # The list comprehension iterates over each row in the dataframe and creates a new Note object with the specified attributes
        note_data = [pretty_midi.Note(velocity=int(row['Velocity']), pitch=int(row['MIDI']), start=row['Start'], end=row['End']) for _, row in dataframe.iterrows()]
        # Return the list of Note objects
        return note_data
    
    @staticmethod
    def csv_to_bend_object(dataframe):
        bend_objects = [pretty_midi.PitchBend(pitch=int(4096 * row['Pitch']), time=row['Start']) for _, row in dataframe[dataframe['Pitch'] != 0.0].iterrows()]
        return bend_objects
    
    def combine_parts(self, *args):
        objects = [self.kwargs.get(args[i]) for i, _ in enumerate(self.kwargs)]
        indices = [i for i, kwarg in enumerate(self.kwargs.keys()) if kwarg in args]
        combined_notes_data = pandas.concat([self.normalized_parts_data[i] for i in indices])
        combined_notes_data = self.group_by_start_with_pitch(combined_notes_data)
        combined_notes_data = self.get_max_end_value(combined_notes_data)
        combined_notes_data = self.update_end_value(combined_notes_data)
        combined_notes_data = self.expand_midi_lists(combined_notes_data)
        if all(isinstance(obj, Monophonic) for obj in objects):
            combined_notes_data = self.group_by_start_with_pitch(combined_notes_data)
            combined_notes_data = self.get_lowest_midi_with_pitch(combined_notes_data)
            combined_notes_data = self.check_and_close_intervals(combined_notes_data)
            combined_notes_data = self.adjust_midi_range(combined_notes_data)
            combined_notes_data = self.combine_consecutive_midi_values_with_pitch(combined_notes_data)
            # print(combined_notes_data)
            out_of_range = combined_notes_data[(combined_notes_data['MIDI'] < 0) | (combined_notes_data['MIDI'] > 127)]
            print(out_of_range)
            combined_notes_data = self.convert_lists_to_scalars(combined_notes_data)
        self.instrumentation = self.filter_first_match(self.instrumentation, indices)
        filtered_notes_data = self.filter_first_match(self.normalized_parts_data, indices)
        filtered_notes_data[indices[0]] = combined_notes_data
        self.normalized_parts_data = filtered_notes_data
        # # Is there be a nondestructive way to align kwargs with newly ready to combine state?
        for arg in args[1:]:
            del self.kwargs[arg]
                
    @staticmethod
    def get_max_end_value(dataframe):
        dataframe = dataframe.copy()
        dataframe['End'] = dataframe['End'].apply(lambda x: max(x) if isinstance(x, list) else x)
        return dataframe
    
    @staticmethod
    def update_end_value(dataframe):
        dataframe = dataframe.copy()
        dataframe['End'] = numpy.minimum(dataframe['Start'].shift(-1), dataframe['End'])
        dataframe = dataframe.iloc[:-1]
        return dataframe
    
    @staticmethod
    def expand_midi_lists(dataframe):
        dataframe = dataframe.copy()
        dataframe['Velocity'] = dataframe['Velocity'].apply(lambda x: x[0] if isinstance(x, list) else x)
        dataframe['Pitch'] = dataframe['Pitch'].apply(lambda x: x[0] if isinstance(x, list) else x)
        start_not_lists = dataframe[~dataframe['MIDI'].apply(lambda x: isinstance(x, list))]
        start_lists = dataframe[dataframe['MIDI'].apply(lambda x: isinstance(x, list))]
        start_lists = start_lists.explode('MIDI')
        start_lists = start_lists.reset_index(drop=True)
        result = pandas.concat([start_not_lists, start_lists], axis=0, ignore_index=True)
        result.sort_values('Start', inplace=True)
        result.reset_index(drop=True, inplace=True)
        return result
    
    @staticmethod
    def filter_first_match(objects, indices):
        updated_objects = []
        first_match_found = False
        for i, obj in enumerate(objects):
            if i in indices and not first_match_found:
                updated_objects.append(obj)
                first_match_found = True
            elif i not in indices:
                updated_objects.append(obj)
        return updated_objects
    
class Texture(Composition):
    grid_history = []
    texture_id = 1
        
    def __init__(self, sivs, grid=None, midi=None, form=None):
        self.grid = fractions.Fraction(grid) if grid is not None else fractions.Fraction(1, 1)
        self.midi = midi if midi is not None else [45, 46, 47, 48, 49]
        self.form = self.select_form(sivs, form if form is not None else 'Prime')
        self.intervals = self.find_indices(self.form, 1)
        self.period = len(self.form[0])
        self.factors = self.get_factors(self.period) 
        self.grid_history.append(self.grid)
        self.texture_id = Texture.texture_id
        Texture.texture_id += 1
        
    def select_form(self, sivs, form):
        binary = self.get_binary(sivs)
        forms = {
            'Prime': lambda bin: bin,
            'Inversion': lambda bin: [1 if x == 0 else 0 for x in bin],
            'Retrograde': lambda bin: bin[::-1],
            'Retrograde-Inversion': lambda bin: [1 if x == 0 else 0 for x in bin][::-1]
        }
        return [forms[form](bin) for bin in binary]
    
    def find_indices(self, binary_lists, target):
        indexes = []
        for i in range(len(binary_lists)):
            ind = []
            for j in range(len(binary_lists[i])):
                if binary_lists[i][j] == target:
                    ind.append(j)
            indexes.append(ind)
        return indexes
    
    @staticmethod
    def get_factors(num):
        factors = []
        i = 1
        while i <= num:
            if num % i == 0:
                factors.append(i)
            i += 1
        return factors
    
    def get_binary(self, sivs):
        binary = []
        if isinstance(sivs, tuple):
            periods = []
            objects = []
            for siv in sivs:
                obj = music21.sieve.Sieve(siv)
                objects.append(obj)
                periods.append(obj.period())
            lcm = self.get_least_common_multiple(periods)
            for obj in objects:
                obj.setZRange(0, lcm - 1)
                binary.append(obj.segment(segmentFormat='binary'))
        else:
            object = music21.sieve.Sieve(sivs)
            object.setZRange(0, object.period() - 1)
            binary.append(object.segment(segmentFormat='binary'))
        return binary
    
    def get_least_common_multiple(self, nums):
        if len(nums) == 2:
            return nums[0] * nums[1] // math.gcd(nums[0], nums[1])
        elif len(nums) > 2:
            middle = len(nums) // 2
            left_lcm = self.get_least_common_multiple(nums[:middle])
            right_lcm = self.get_least_common_multiple(nums[middle:])
            return left_lcm * right_lcm // math.gcd(left_lcm, right_lcm)
        else:
            return nums[0]
        
    def get_largest_prime_factor(self, num):
        for i in range(1, int(num ** 0.5) + 1):
            if num % i == 0:
                factor = num // i
                if self.is_prime(factor):
                    return factor
                elif self.is_prime(i):
                    return i
        return num
    
    @staticmethod
    def is_prime(num):
        if num < 2:
            return False
        for i in range(2, num):
            if num % i == 0:
                return False
        return True
    
    @staticmethod
    def octave_interpolation(intervals):
        set = []
        mod12 = list(range(12))
        for i in intervals:
            siv = []
            for j in i:
                siv.append(mod12[j % len(mod12)])
            set.append(siv)
        return set
    
    @staticmethod
    def segment_octave_by_period(period):
        interval = decimal.Decimal('12') / decimal.Decimal(str(period))
        return [interval * decimal.Decimal(str(i)) for i in range(period)]
    
    @staticmethod
    def parse_pitch_data(dataframe):
        # Compute 'Pitch' and 'MIDI' columns for each row
        for index, row in dataframe.iterrows():
            pitch = round(row['MIDI'] - math.floor(row['MIDI']), 4)
            midi = math.floor(row['MIDI'])
            dataframe.at[index, 'MIDI'] = midi
            dataframe.at[index, 'Pitch'] = pitch
        # Reorder the columns
        column_order = ['Velocity', 'MIDI', 'Pitch', 'Start', 'End']
        dataframe = dataframe.reindex(columns=column_order)
        # Return the updated dataframe
        return dataframe
    
    # @staticmethod
    # def parse_pitch_data(dataframe):
    #     pitch_data = []
    #     for _, row in dataframe.iterrows():
    #         row['Pitch'] = row['MIDI'].apply(lambda x: round(x - math.floor(x), 4))
    #         row['MIDI'] = row['MIDI'].apply(lambda x: math.floor(x))
    #         pitch_data.append(row)
    #     return pitch_data
    
class NonPitched(Texture):
    part_id = 1 # First instance has ID of 1.
    
    def __init__(self, sivs, grid=None, midi=None, form=None):
        super().__init__(sivs, grid, midi, form)
        self.name = 'NonPitched' # Set name of instrument.
        self.part_id = NonPitched.part_id # Set ID value.
        NonPitched.part_id += 1 # Increment ID value.
        self.create_part()
        
    def create_part(self):
        notes_data = []
        for i in range(len(self.form)):
            midi_pool = itertools.cycle(self.midi_pool(i))
            for j in range(len(self.factors)):
                pattern = numpy.tile(self.form[i], self.factors[j])
                indices = numpy.nonzero(pattern)[0]
                duration = self.grid * (self.period / self.factors[j])
                for k in indices:
                    velocity = 127
                    offset = k * duration
                    notes_data.append([velocity, next(midi_pool), offset, offset + self.grid])
        notes_data = [[data[0], data[1], round(data[2], 6), round(data[3], 6)] for data in notes_data]
        self.notes_data = pandas.DataFrame(notes_data, columns=['Velocity', 'MIDI', 'Start', 'End']).sort_values(by = 'Start').drop_duplicates()
        
    def midi_pool(self, index):
        events = self.form[index].count(1)
        largest_prime_slice = slice(0, self.get_largest_prime_factor(events))
        pool = itertools.cycle(self.midi[largest_prime_slice])
        return [next(pool) for _ in range(events)]
    
class Monophonic(Texture):
    part_id = 1 # First instance has ID of 1.
    
    def __init__(self, sivs, grid=None, midi=None, form=None):
        super().__init__(sivs, grid, midi, form)
        self.name = 'Monophonic' # Set name of texture.
        self.part_id = Monophonic.part_id # Set ID value.
        Monophonic.part_id += 1 # Increment ID value.
        self.closed_intervals = self.octave_interpolation(self.intervals) # Contain all intervals within a mod12 continuum. 
        self.create_part() # Call the create_Texture method.
        
    def create_part(self):
        notes_data = [] # A list container for notes_data.
        for i in range(len(self.form)): # Set an iterator for each sieve represented in self.form.
            # midi_pool = itertools.cycle(self.midi_pool(i)) # Create a midi_pool for each sieve represented in self.form.
            midi_pool = itertools.cycle(self.generate_midi_pool(i))
            for j in range(len(self.factors)): # Set an iterator for each sieve based on the factorization of self.period.
                pattern = numpy.tile(self.form[i], self.factors[j]) # Repeat form a number of times sufficient to normalize pattern length against sieves represented in self.form.
                indices = numpy.nonzero(pattern)[0] # Create a list of indicies where non-zero elements occur within the pattern.
                multiplier = self.period / self.factors[j] # Find the number of repititions required to achieve periodicity per sieve represented in self.form.
                duration = self.grid * multiplier # Find the duration of each note represented as a float.
                for k in indices: # For each non-zero indice append notes_data list with cooresponding midi information.
                    velocity = 127
                    offset = k * duration
                    notes_data.append([velocity, next(midi_pool), offset, offset + self.grid])
        notes_data = [[data[0], data[1], round(data[2], 6), round(data[3], 6)] for data in notes_data]
        self.notes_data = pandas.DataFrame(notes_data, columns=['Velocity', 'MIDI', 'Start', 'End']).sort_values(by = 'Start').drop_duplicates()
        self.notes_data = self.group_by_start(self.notes_data)
        self.notes_data = self.get_lowest_midi(self.notes_data)
        self.notes_data = self.close_intervals(self.notes_data)
        self.notes_data = self.combine_consecutive_midi_values(self.notes_data)
        self.notes_data = self.convert_lists_to_scalars(self.notes_data)
        self.notes_data = self.parse_pitch_data(self.notes_data)
        
    # How to use the referenced sieve to select row form?
    # How to use number of needed events to generate exactly the correct amount of pitch data needed?
    # midi_pool represents a sequence of pitch data that is repeated until the required number of notes needed has been satisfied.
    # How does the number of needed notes relate to the pool data? How does the pool data relate to the matrix of intervals?
    # What about using the select_form method to determine row selection?
    
    def generate_midi_pool(self, form_index):
        tonality = 40
        pitch = tonality + self.closed_intervals[form_index][0]
        indices = numpy.nonzero(self.form[form_index])[0]
        segment = self.segment_octave_by_period(self.period)
        intervals = [segment[i] for i in indices]
        matrix = pitch + Composition.generate_pitchclass_matrix(intervals)
        combo = [matrix.iloc[i].values.tolist() for i, _ in enumerate(matrix)] + [matrix.iloc[:, i].values.tolist() for i, _ in enumerate(matrix)]
        pool = list(itertools.chain(*combo))
        return pool
    
# Monophonic
# Homophonic
# Polyphonic
# Heterophonic
    
if __name__ == '__main__':
    sivs = '((8@0|8@1|8@7)&(5@1|5@3))', '((8@0|8@1|8@2)&5@0)', '((8@5|8@6)&(5@2|5@3|5@4))', '(8@6&5@1)', '(8@3)', '(8@4)', '(8@1&5@2)'
    voices = {
        'mono1': Monophonic(sivs),
        'mono2': Monophonic(sivs, '4/3')
    }
    
    score = Score(**voices)
    score.combine_parts('mono1', 'mono2')
    score.write_score()