import music21
import pretty_midi
import fractions
import itertools
import functools
import pandas
import numpy
import math

class Score:
    def __init__(self, *args):
        self.args = args
        self.normalized_numerators = numpy.array([self._normalize_numerator(arg, self._get_multiplier(arg)) for arg in self.args])
        self.multipliers = self.args[-1]._get_least_common_multiple(self.normalized_numerators) // self.normalized_numerators
        self.normalized_parts_data = self.normalize_periodicity()
            
    def create_score(self):
        score = pretty_midi.PrettyMIDI()
        score.time_signature_changes.append(pretty_midi.TimeSignature(5,4,0))
        score.resolution = score.resolution * 2
        notes_list = self.combine_parts(self.normalized_parts_data)
        notes = self._csv_to_midi(notes_list)
        instrument = pretty_midi.Instrument(program=0, name=f'{arg.name}')
        instrument.notes = notes
        score.instruments.append(instrument)
        print('Build Complete')
        return score
    
    def normalize_periodicity(self):
        normalized_parts_data = []
        for arg, multiplier in zip(self.args, self.multipliers):
            duplicates = [arg.notes_data.copy()]
            length_of_one_rep = math.pow(arg.period, 2)
            for i in range(multiplier):
                df_copy = arg.notes_data.copy()
                df_copy['Start'] = round(df_copy['Start'] + (length_of_one_rep * arg.grid) * i, 6)
                df_copy['End'] = round(df_copy['End'] + (length_of_one_rep * arg.grid) * i, 6)
                duplicates.append(df_copy)
            result = pandas.concat(duplicates)
            result = result.drop_duplicates()
            Utility.save_as_csv(result, f'Normalized {arg.name} Part {arg.id}')
            normalized_parts_data.append(result)
        return normalized_parts_data
    
    def combine_parts(*part_objs):
        parts = Score(*part_objs)
    # def combine_parts(self, parts):
        part = pandas.concat(parts.normalized_parts_data)
        part = Score._group_by_start(part)
        part = Score._get_max_end_value(part)
        part = Score._update_end_value(part)
        part = Score._expand_midi_lists(part)
        part = Score._convert_velocity_to_scalar(part)
        Utility.save_as_csv(part, f'Combined Part')
        return part
    
    def _group_by_start(dataframe):
        # Set is used to automatically remove duplicate values from the list
        grouped_velocity = dataframe.groupby('Start')['Velocity'].apply(lambda x: sorted(list(set(x))))
        grouped_midi = dataframe.groupby('Start')['MIDI'].apply(lambda x: sorted(list(set(x))))
        grouped_end = dataframe.groupby('Start')['End'].apply(lambda x: sorted(list(set(x))))
        result = pandas.concat([grouped_velocity, grouped_midi, grouped_end], axis=1).reset_index()
        result = result[['Velocity', 'MIDI', 'Start', 'End']]
        return result
    
    def _get_max_end_value(dataframe):
        dataframe = dataframe.copy()
        dataframe['End'] = dataframe['End'].apply(lambda x: max(x) if type(x) == list else x)
        return dataframe
    
    def _update_end_value(dataframe):
        dataframe = dataframe.copy()
        for i in range(len(dataframe) - 1):
            if dataframe.loc[i + 1, 'Start'] < dataframe.loc[i, 'End']:
                dataframe.loc[i, 'End'] = dataframe.loc[i + 1, 'Start']
        return dataframe
    
    def _expand_midi_lists(dataframe):
        result = pandas.DataFrame(columns=['Velocity', 'MIDI', 'Start', 'End'])
        for _, row in dataframe.iterrows():
            midi = row['MIDI']
            start = row['Start']
            end = row['End']
            velocity = row['Velocity']
            if isinstance(midi, list):
                intermediate_df = pandas.DataFrame({'Velocity': [velocity] * len(midi),
                                                    'MIDI': midi, 
                                                    'Start': [start + i for i in range(len(midi))], 
                                                    'End': [end + i for i in range(len(midi))]})
                result = pandas.concat([result, intermediate_df], ignore_index=True)
            else:
                result = pandas.concat([result, pandas.DataFrame({'Velocity': [velocity], 'MIDI': [midi], 'Start': [start], 'End': [end]})], ignore_index=True)
        return result
    
    def _convert_velocity_to_scalar(dataframe):
        dataframe['Velocity'] = dataframe['Velocity'].apply(lambda x: x[0])
        return dataframe
    
    def _get_multiplier(self, arg):
        #should I add grid history to the datad
        lcd = functools.reduce(math.lcm, (fraction.denominator for fraction in arg.grid_history))
        return [lcd // fraction.denominator for fraction in arg.grid_history][arg.id-1]
    
    def _normalize_numerator(self, arg, mult):
        return arg.grid_history[arg.id-1].numerator * mult
    
    def _csv_to_midi(dataframe):
        dataframe = dataframe.groupby('MIDI', group_keys=True).apply(lambda x: x.assign(velocity=x.Velocity, start=x.Start, end=x.End))
        return [pretty_midi.Note(velocity=int(row['velocity']), pitch=int(row['MIDI']), start=row['start'], end=row['end']) for _, row in dataframe.iterrows()]
    
class Part:
    grid_history = []
        
    def __init__(self, sivs, grid=None, midi=None, form=None):
        self.grid = fractions.Fraction(grid) if grid is not None else fractions.Fraction(1, 1)
        self.midi = midi if midi is not None else [45, 46, 47, 48, 49]
        self.form = self._select_form(sivs, form if form is not None else 'Prime')
        self.intervals = self._find_indices(self.form, 1)
        self.period = len(self.form[0])
        self.factors = self._get_factors(self.period) 
        self.grid_history.append(self.grid)
        
    def _select_form(self, sivs, form):
        binary = self._get_binary(sivs)
        forms = {
            'Prime': lambda bin: bin,
            'Inversion': lambda bin: [1 if x == 0 else 0 for x in bin],
            'Retrograde': lambda bin: bin[::-1],
            'Retrograde-Inversion': lambda bin: [1 if x == 0 else 0 for x in bin][::-1]
        }
        return [forms[form](bin) for bin in binary]
        
    def _get_binary(self, sivs):
        binary = []
        if isinstance(sivs, tuple):
            periods = []
            objects = []
            for siv in sivs:
                obj = music21.sieve.Sieve(siv)
                objects.append(obj)
                periods.append(obj.period())
            lcm = self._get_least_common_multiple(periods)
            for obj in objects:
                obj.setZRange(0, lcm - 1)
                binary.append(obj.segment(segmentFormat='binary'))
        else:
            object = music21.sieve.Sieve(sivs)
            object.setZRange(0, object.period() - 1)
            binary.append(object.segment(segmentFormat='binary'))
        return binary
    
    def _find_indices(self, binary_lists, target):
        indexes = []
        for i in range(len(binary_lists)):
            ind = []
            for j in range(len(binary_lists[i])):
                if binary_lists[i][j] == target:
                    ind.append(j)
            indexes.append(ind)
        return indexes
    
    def _get_least_common_multiple(self, nums):
        if len(nums) == 2:
            return nums[0] * nums[1] // math.gcd(nums[0], nums[1])
        elif len(nums) > 2:
            middle = len(nums) // 2
            left_lcm = self._get_least_common_multiple(nums[:middle])
            right_lcm = self._get_least_common_multiple(nums[middle:])
            return left_lcm * right_lcm // math.gcd(left_lcm, right_lcm)
        else:
            return nums[0]
        
    def _get_largest_prime_factor(self, num):
        for i in range(1, int(num ** 0.5) + 1):
            if num % i == 0:
                factor = num // i
                if self._is_prime(factor):
                    return factor
                elif self._is_prime(i):
                    return i
        return num
    
    def _octave_interpolation(intervals):
        set = []
        mod12 = list(range(12))
        for i in intervals:
            siv = []
            for j in i:
                siv.append(mod12[j % len(mod12)])
            set.append(siv)
        return set
    
    def _combine_consecutive_midi_values(dataframe):
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
    
    def _get_lowest_midi(dataframe):
        dataframe['MIDI'] = dataframe['MIDI'].apply(lambda x: min(x) if x else None)
        dataframe = dataframe.dropna(subset=['MIDI'])
        return dataframe[['Velocity', 'MIDI', 'Start', 'End']]
    
    def _is_prime(self, num):
        if num < 2:
            return False
        for i in range(2, num):
            if num % i == 0:
                return False
        return True
    
    def _get_factors(self, num):
        factors = []
        i = 1
        while i <= num:
            if num % i == 0:
                factors.append(i)
            i += 1
        return factors
    
class Percussion(Part):
    id = 1
    
    def __init__(self, sivs, grid=None, midi=None, form=None):
        super().__init__(sivs, grid, midi, form)
        self.name = 'Percussion'
        self.id = Percussion.id
        Percussion.id += 1
        self._create_part()
        
    def _create_part(self):
        notes_data = []
        for i in range(len(self.form)):
            midi_pool = itertools.cycle(self._midi_pool(i))
            for j in range(len(self.factors)):
                pattern = numpy.tile(self.form[i], self.factors[j])
                indices = numpy.nonzero(pattern)[0]
                dur = self.grid * (self.period / self.factors[j])
                for k in indices:
                    velocity = 127
                    offset = k * dur
                    notes_data.append([velocity, next(midi_pool), offset, offset + self.grid])
        notes_data = [[data[0], data[1], round(data[2], 6), round(data[3], 6)] for data in notes_data]
        self.notes_data = pandas.DataFrame(notes_data, columns=['Velocity', 'MIDI', 'Start', 'End']).sort_values(by = 'Start').drop_duplicates()
        # self.notes_data = Utility.rearrange_columns(self.notes_data,'MIDI', 'Velocity', 'Start', 'End')
        Utility.save_as_csv(self.notes_data, f'{self.name} Part {self.id}')
        
    def _midi_pool(self, index):
        events = self.form[index].count(1)
        largest_prime_slice = slice(0, self._get_largest_prime_factor(events))
        instrument_pool = itertools.cycle(self.midi[largest_prime_slice])
        return [next(instrument_pool) for _ in range(events)]
    
class Bass(Part):
    id = 1
    
    def __init__(self, sivs, grid=None, midi=None, form=None):
        super().__init__(sivs, grid, midi, form)
        self.name = 'Bass'
        self.id = Bass.id
        Bass.id += 1
        self._create_part()
        
    def _create_part(self):
        notes_data = []
        for i in range(len(self.form)):
            midi_pool = itertools.cycle(self._midi_pool(i))
            for j in range(len(self.factors)):
                pattern = numpy.tile(self.form[i], self.factors[j])
                indices = numpy.nonzero(pattern)[0]
                dur = self.grid * (self.period / self.factors[j])
                for k in indices:
                    velocity = 127
                    offset = k * dur
                    notes_data.append([velocity, next(midi_pool), offset, offset + self.grid])
        notes_data = [[data[0], data[1], round(data[2], 6), round(data[3], 6)] for data in notes_data]
        self.notes_data = pandas.DataFrame(notes_data, columns=['Velocity', 'MIDI', 'Start', 'End']).sort_values(by = 'Start').drop_duplicates()
        # self.notes_data = Utility._group_by_midi(self.notes_data)
        self.notes_data = self._group_by_start(self.notes_data)
        self.notes_data = self._combine_consecutive_midi_values(self.notes_data)
        self.notes_data = self._get_lowest_midi(self.notes_data)
        self.notes_data = Utility.rearrange_columns(self.notes_data,'MIDI', 'Velocity', 'Start', 'End')
        Utility.save_as_csv(self.notes_data, f'{self.name} Part {self.id}')
        
    def _midi_pool(self, index):
        pitch_class = self._octave_interpolation(self.intervals)
        tonality = 40
        pool = [pitch + tonality for pitch in pitch_class[index]]
        return pool
    
# Map intervals onto mod-12 semitones, then map again on those intervals to create chords.
# A better solution may be to utilize the approach to consolidating datapoints as in the Bass class to create a counterpoint
class Keyboard(Part):
    id = 1
    
    def __init__(self, sivs, grid=None, midi=None, form=None):
        super().__init__(sivs, grid, midi, form)
        self.name = 'Keyboard'
        self.id = Keyboard.id
        Keyboard.id += 1
        self._create_part()
        
    def _create_part(self):
        notes_data = []
        for i in range(len(self.form)):
            midi_pool = itertools.cycle(self._midi_pool(i))
            for j in range(len(self.factors)):
                pattern = numpy.tile(self.form[i], self.factors[j])
                indices = numpy.nonzero(pattern)[0]
                dur = self.grid * (self.period / self.factors[j])
                for k in indices:
                    velocity = 127
                    offset = k * dur
                    notes_data.append([velocity, next(midi_pool), offset, offset + self.grid])
        notes_data = [[data[0], data[1], round(data[2], 6), round(data[3], 6)] for data in notes_data]
        self.notes_data = pandas.DataFrame(notes_data, columns=['Velocity', 'MIDI', 'Start', 'End']).sort_values(by = 'Start').drop_duplicates()
        
    def _midi_pool(self, index):
        pitch_class = self._octave_interpolation(self.intervals)
        tonality = 40
        pool = [pitch + tonality for pitch in pitch_class[index]]
        return pool
    
class Utility:
    @staticmethod
    def _group_by_midi(dataframe):
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
    
    @staticmethod
    def rearrange_columns(dataframe, *column_names):
        return dataframe[list(column_names)]
    
    @staticmethod
    def save_as_csv(dataframe, filename):
        dataframe.sort_values(by = 'Start').to_csv(f'sifters/.{filename}.csv', index=False)
        
    @staticmethod
    def save_as_midi(pretty_midi_obj, filename):
        pretty_midi_obj.write(f'sifters/.{filename}.mid')
            
        # is it possible to make multiple grids within one instance of a part class
if __name__ == '__main__':
    sivs = '((8@0|8@1|8@7)&(5@1|5@3))', '((8@0|8@1|8@2)&5@0)', '((8@5|8@6)&(5@2|5@3|5@4))', '(8@6&5@1)', '(8@3)', '(8@4)', '(8@1&5@2)'
    perc1 = Percussion(sivs)
    perc2 = Percussion(sivs, '4/3')
    # perc = Part._combine_dataframes(perc1.notes_data, perc2.notes_data)
    # perc = Part._group_by_start(perc)
    # perc = Part._get_max_end_value(perc)
    # perc = Part._update_end_value(perc)
    # # perc = Part.combine_parts(perc1, perc2)
    # Utility.save_as_csv(perc, 'combined df')
    perc = Score.combine_parts(perc1, perc2)
    # score = Score(perc)
    score = perc.create_score()
    Utility.save_as_midi(score, 'score')
    # print(score)
    # print(score.args[1].notes_data)