import music21
import pretty_midi
import fractions
import itertools
import functools
import pandas
import numpy
import math

class Composition:
    def generate_relative_matrix(intervals):
        row = []
        columns = []
        for tone in intervals:
            interval = (tone - intervals[0])
            row.append(interval)
            columns.append([(intervals[0] + (intervals[0] - tone))] * len(intervals))
        for i, _ in enumerate(row):
            for j, _ in enumerate(row):
                print(row[i] + columns[i][j])
        return numpy.add(row, columns)

    # def generate_serial_matrix(intervals):
    #     current = intervals[:-1]
    #     next = intervals[1:]
    #     row = [0] + [abs(current[0] - next[i]) for i, _ in enumerate(current)]
    #     matrix = [[abs(note - 12) % 12] for note in row]
    #     matrix = [r * len(intervals) for r in matrix]
    #     matrix = [[(matrix[i][j] + row[j]) % 12 for j, _ in enumerate(range(len(row)))] for i in range(len(intervals))]
    #     matrix = pandas.DataFrame(matrix, index=[f"P{m[0]}" for m in matrix], columns=[f"I{i}" for i in matrix[0]])
    #     Utility.save_as_csv(matrix, f'serial matrix {intervals}')
    #     inverted_matrix = ([matrix.iloc[:, i].values.tolist() for i, _ in enumerate(matrix)])
    #     return matrix

    def generate_serial_matrix(intervals):
        current = intervals[:-1]
        next = intervals[1:]
        row = [0] + [next[i] - current[0] for i, _ in enumerate(current)]
        matrix = [[abs(note - 12) % 12] for note in row]
        matrix = [r * len(intervals) for r in matrix]
        matrix = [[(matrix[i][j] + row[j]) % 12 for j, _ in enumerate(range(len(row)))] for i in range(len(intervals))]
        matrix = pandas.DataFrame(matrix)
        return matrix
    
    @staticmethod
    def group_by_start(dataframe):
        grouped_velocity = dataframe.groupby('Start')['Velocity'].apply(lambda x: sorted(set(x)))
        grouped_midi = dataframe.groupby('Start')['MIDI'].apply(lambda x: sorted(set(x)))
        grouped_end = dataframe.groupby('Start')['End'].apply(lambda x: sorted(set(x)))
        result = pandas.concat([grouped_velocity, grouped_midi, grouped_end], axis=1).reset_index()
        result = result[['Velocity', 'MIDI', 'Start', 'End']]
        return result
    
    @staticmethod
    def get_lowest_midi(dataframe):
        dataframe['MIDI'] = dataframe['MIDI'].apply(lambda x: min(x) if x else None)
        dataframe = dataframe.dropna(subset=['MIDI'])
        return dataframe[['Velocity', 'MIDI', 'Start', 'End']]
    
    def check_and_close_intervals(self, dataframe):
        for i in range(len(dataframe['MIDI']) - 1):
            if abs(dataframe['MIDI'][i] - dataframe['MIDI'][i + 1]) > 6:
                dataframe = self.close_intervals(dataframe)
                return self.check_and_close_intervals(dataframe)
        return dataframe
    
    @staticmethod
    def close_intervals(dataframe):
        updated_df = dataframe.copy()
        for i, midi in enumerate(updated_df["MIDI"][:-1]):
            next_midi = updated_df["MIDI"][i + 1]
            if midi - next_midi > 6:
                updated_df.at[i + 1, "MIDI"] = next_midi + 12
            elif midi - next_midi < -6:
                updated_df.at[i + 1, "MIDI"] = next_midi - 12
        return updated_df
    
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
    def convert_lists_to_scalars(dataframe):
        for col in dataframe.columns:
            if dataframe[col].dtype == object:
                dataframe[col] = dataframe[col].apply(lambda x: x[0])
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
        normalized_parts_data = []
        for arg, multiplier in zip(self.kwargs.values(), self.multipliers):
            duplicates = [arg.notes_data.copy()]
            length_of_one_rep = math.pow(arg.period, 2)
            for i in range(multiplier):
                dataframe_copy = arg.notes_data.copy()
                dataframe_copy['Start'] = round(dataframe_copy['Start'] + (length_of_one_rep * arg.grid) * i, 6)
                dataframe_copy['End'] = round(dataframe_copy['End'] + (length_of_one_rep * arg.grid) * i, 6)
                duplicates.append(dataframe_copy)
            result = pandas.concat(duplicates)
            result = result.drop_duplicates()
            normalized_parts_data.append(result)
        self.normalized_parts_data = normalized_parts_data
        
    def write_score(self):
        score = pretty_midi.PrettyMIDI()
        # Write method to determine TimeSignature
        score.time_signature_changes.append(pretty_midi.TimeSignature(5, 4, 0))
        score.resolution = score.resolution * 2
        midi_data = [self.csv_to_midi(part) for part in self.normalized_parts_data]
        for i, _ in enumerate(midi_data):
            self.instrumentation[i].notes = midi_data[i]
            score.instruments.append(self.instrumentation[i])
        score.write(f'sifters/.score.mid')
    
    @staticmethod
    def csv_to_midi(dataframe):
        dataframe = dataframe.groupby('MIDI', group_keys=True).apply(lambda x: x.assign(velocity=x.Velocity, start=x.Start, end=x.End))
        return [pretty_midi.Note(velocity=int(row['velocity']), pitch=int(row['MIDI']), start=row['start'], end=row['end']) for _, row in dataframe.iterrows()]
        
    def combine_parts(self, *args):
        objects = [self.kwargs.get(args[i]) for i, _ in enumerate(self.kwargs)]
        indices = [i for i, kwarg in enumerate(self.kwargs.keys()) if kwarg in args]
        combined_notes_data = pandas.concat([self.normalized_parts_data[i] for i in indices])
        combined_notes_data = self.group_by_start(combined_notes_data)
        combined_notes_data = self.get_max_end_value(combined_notes_data)
        combined_notes_data = self.update_end_value(combined_notes_data)
        combined_notes_data = self.expand_midi_lists(combined_notes_data)
        if all(isinstance(obj, Bass) for obj in objects):
            combined_notes_data = self.group_by_start(combined_notes_data)
            combined_notes_data = self.get_lowest_midi(combined_notes_data)
            combined_notes_data = self.check_and_close_intervals(combined_notes_data)
            combined_notes_data = self.combine_consecutive_midi_values(combined_notes_data)
            combined_notes_data = self.convert_lists_to_scalars(combined_notes_data)
        Utility.save_as_csv(combined_notes_data, 'combined')
        self.instrumentation = self.filter_first_match(self.instrumentation, indices)
        filtered_notes_data = self.filter_first_match(self.normalized_parts_data, indices)
        filtered_notes_data[indices[0]] = combined_notes_data
        self.normalized_parts_data = filtered_notes_data
        # Is there be a nondestructive way to align kwargs with newly ready to combine state?
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
    
class Part(Composition):
    grid_history = []
    part_id = 1
        
    def __init__(self, sivs, grid=None, midi=None, form=None):
        self.grid = fractions.Fraction(grid) if grid is not None else fractions.Fraction(1, 1)
        self.midi = midi if midi is not None else [45, 46, 47, 48, 49]
        self.form = self.select_form(sivs, form if form is not None else 'Prime')
        self.intervals = self.find_indices(self.form, 1)
        self.period = len(self.form[0])
        self.factors = self.get_factors(self.period) 
        self.grid_history.append(self.grid)
        self.part_id = Part.part_id
        Part.part_id += 1
        
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
    
class Percussion(Part):
    instrument_id = 1
    
    def __init__(self, sivs, grid=None, midi=None, form=None):
        super().__init__(sivs, grid, midi, form)
        self.name = 'Percussion'
        self.instrument_id = Percussion.instrument_id
        Percussion.instrument_id += 1
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
        Utility.save_as_csv(self.notes_data, f'Init {self.name} {self.instrument_id}')
        
    def midi_pool(self, index):
        events = self.form[index].count(1)
        largest_prime_slice = slice(0, self.get_largest_prime_factor(events))
        pool = itertools.cycle(self.midi[largest_prime_slice])
        return [next(pool) for _ in range(events)]
    
class Bass(Part):
    instrument_id = 1
    
    def __init__(self, sivs, grid=None, midi=None, form=None):
        super().__init__(sivs, grid, midi, form)
        self.name = 'Bass'
        self.instrument_id = Bass.instrument_id
        Bass.instrument_id += 1
        self.closed_intervals = self.octave_interpolation(self.intervals)
        self.create_part()
        # m = [Composition.generate_relative_matrix([note + 40 for note in self.closed_intervals[i]]) for i, _ in enumerate(range(len(self.closed_intervals)))]
        # m = [Composition.generate_serial_matrix([note + 40 for note in self.closed_intervals[i]]) for i, _ in enumerate(range(len(self.closed_intervals)))]
        m = Composition.generate_serial_matrix
        # print(m)
        
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
        self.notes_data = self.group_by_start(self.notes_data)
        self.notes_data = self.get_lowest_midi(self.notes_data)
        self.notes_data = self.close_intervals(self.notes_data)
        self.notes_data = self.combine_consecutive_midi_values(self.notes_data)
        self.notes_data = self.convert_lists_to_scalars(self.notes_data)
        Utility.save_as_csv(self.notes_data, f'Init {self.name} {self.instrument_id}')
            
    def midi_pool(self, index):
        tonality = 40
        pool = [pitch + tonality for pitch in self.closed_intervals[index]]
        # print(pool)
        print(self.closed_intervals[index])
        matrix = Composition.generate_serial_matrix(self.closed_intervals[index])
        print(matrix)
        # print([matrix.iloc[:, i].values.tolist() for i, _ in enumerate(matrix)])
        return pool
    
# Map intervals onto mod-12 semitones, then map again on those intervals to create chords.
# A better solution may be to utilize the approach to consolidating datapoints as in the Bass class to create a counterpoint
class Keyboard(Part):
    instrument_id = 1
    
    def __init__(self, sivs, grid=None, midi=None, form=None):
        super().__init__(sivs, grid, midi, form)
        self.name = 'Keyboard'
        self.instrument_id = Keyboard.instrument_id
        
        Keyboard.instrument_id += 1
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
        pitch_class = self.octave_interpolation(self.intervals)
        tonality = 40
        pool = [pitch + tonality for pitch in pitch_class[index]]
        return pool
    
class Utility:
    def group_by_midi(dataframe):
        result = {}
        for _, row in dataframe.iterrows():
            velocity = row['Velocity']
            midi = row['MIDI']
            start = row['Start']
            end = row['End']
            midi_str = str(midi)
            if midi_str in result:
                result[midi_str]['Velocity'].append(velocity)
                result[midi_str]['Start'].append(start)
                result[midi_str]['End'].append(end)
            else:
                result[midi_str] = {'Velocity': [velocity], 'Start': [start], 'End': [end]}
        result = pandas.DataFrame(result).transpose()
        result['MIDI'] = result.index
        result.reset_index(drop=True, inplace=True)
        result = result[['Velocity', 'MIDI', 'Start', 'End']]
        return result
    
    def rearrange_columns(dataframe, *column_names):
        return dataframe[list(column_names)]
    
    def save_as_csv(dataframe, filename):
        dataframe.to_csv(f'sifters/.{filename}.csv', index=True)
        
if __name__ == '__main__':
    # sivs = '((8@0|8@1|8@7)&(5@1|5@3))'
    sivs = '((8@0|8@1|8@7)&(5@1|5@3))', '((8@0|8@1|8@2)&5@0)', '((8@5|8@6)&(5@2|5@3|5@4))', '(8@6&5@1)', '(8@3)', '(8@4)', '(8@1&5@2)'
    instruments = {
        # 'perc1': Percussion(sivs),
        # 'perc2': Percussion(sivs, '2/3'),
        # 'perc3': Percussion(sivs, '4/5'),
        'bass1': Bass(sivs, '4/3'),
        # 'bass2': Bass(sivs, '2'),
        # 'bass3': Bass(sivs, '8/3')
    }
    
    score = Score(**instruments)
    # What if I want to combine different subsections if the instrumentation (bass, percussion)
    # score.combine_parts('perc1', 'perc2', 'perc3')
    # score.combine_parts('bass1', 'bass2', 'bass3')
    # score.write_score()
    # print(score)