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
        self.normalized_numerators = []
        self.normalized_denominators = []
        self.multipliers = []
            
    def create_score(self):
        score = pretty_midi.PrettyMIDI()
        score.time_signature_changes.append(pretty_midi.TimeSignature(5,4,0))
        score.resolution = score.resolution * 2
        self.normalized_numerators = numpy.array([self._normalize_numerator(arg, self._get_multiplier(arg)) for arg in self.args])
        lcm = self.args[-1]._get_least_common_multiple(self.normalized_numerators)
        self.multipliers = lcm // self.normalized_numerators
        notes_list = []
        instruments = []
        for arg, multiplier in zip(self.args, self.multipliers):
                print(f'Constructing Part {arg.id}')
                norm = self._normalize_periodicity(arg, multiplier)
                notes = self._csv_to_midi(norm)
                notes_list.append(notes)
                instruments.append(pretty_midi.Instrument(program=0, name=f'{arg.name}'))
        for i,arg in enumerate(self.args):
            instruments[i].notes = notes_list[i]
            score.instruments.append(instruments[i])
        print('Build Complete')
        return score
    
    @staticmethod
    def _normalize_periodicity(arg, mult):
        duplicates = [arg.dataframe.copy()]
        length_of_one_rep = math.pow(arg.period, 2)
        for i in range(mult):
            # Put everything that needs to be done on every repeitition within this for loop
            df_copy = arg.dataframe.copy()
            df_copy['Start'] = df_copy['Start'] + (length_of_one_rep * arg.grid) * i
            df_copy['End'] = df_copy['End'] + (length_of_one_rep * arg.grid) * i
            df_copy['MIDI'] = df_copy['MIDI'] + i
            duplicates.append(df_copy)
        result = pandas.concat(duplicates)
        result = result.drop_duplicates()
        Utility.save_as_csv(arg._grouped_by_start(result), f'norm part {arg.id}')     
        return result
    
    @staticmethod
    def _get_multiplier(arg):
        lcd = functools.reduce(math.lcm, (fraction.denominator for fraction in arg.grid_history))
        return [lcd // fraction.denominator for fraction in arg.grid_history][arg.id-1]
    
    @staticmethod
    @functools.lru_cache()
    def _normalize_numerator(arg, mult):
        return arg.grid_history[arg.id-1].numerator * mult
    
    @staticmethod
    @functools.lru_cache()
    def _normalize_denominator(arg, mult):
        return arg.grid_history[arg.id-1].denominator * mult
    
    @staticmethod
    def _csv_to_midi(dataframe):
        dataframe = dataframe.groupby('MIDI', group_keys=True).apply(lambda x: x.assign(start=x.Start, end=x.End))
        return [pretty_midi.Note(velocity=100, pitch=int(row['MIDI']), start=row['start'], end=row['end']) for _, row in dataframe.iterrows()]
    
class Part:
    grid_history = []
    next_id = 1
        
    def __init__(self, sivs, grid=None, midi=None):
        self.intervals = self._get_intervals(sivs)
        self.bin = self._get_binary(sivs)
        self.period = len(self.bin[0])
        self.factors = self._get_factors(self.period)
        self.midi = midi if midi is not None else [45, 46, 47, 48, 49]
        self.grid = fractions.Fraction(grid) if grid is not None else fractions.Fraction(1, 1)
        self.grid_history.append(self.grid)
        self.id = Part.next_id
        self.create_part()
        Part.next_id += 1
        
    @functools.lru_cache()
    def _get_binary(self, sivs):
        bin = []
        if isinstance(sivs, tuple):
            per = []
            obj = []
            for siv in sivs:
                objects = music21.sieve.Sieve(siv)
                obj.append(objects)
                per.append(objects.period())
            lcm = self._get_least_common_multiple(per)
            for o in obj:
                o.setZRange(0, lcm - 1)
                bin.append(o.segment(segmentFormat='binary'))
        else:
            obj = music21.sieve.Sieve(sivs)
            obj.setZRange(0, obj.period() - 1)
            bin.append(obj.segment(segmentFormat='binary'))
        return bin
    
    @functools.lru_cache()
    def _get_intervals(self, sivs):
        intervals = []
        for siv in sivs:
            set = music21.sieve.Sieve(siv)
            set.setZRange(0, set.period() - 1)
            intervals.append(set.segment())
        return intervals
    
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
    
    @staticmethod
    def _octave_interpolation(intervals):
        set = []
        mod12 = list(range(12))
        for i in intervals:
            siv = []
            for j in i:
                siv.append(mod12[j % len(mod12)])
            set.append(siv)
        return set
    
    @staticmethod
    def _grouped_by_start(dataframe):
        grouped_end = dataframe.groupby('Start')['End'].apply(lambda x: x.iloc[0])
        grouped_midi = dataframe.groupby('Start')['MIDI'].apply(lambda x: sorted(list(x)))
        result = pandas.concat([grouped_end, grouped_midi], axis=1).reset_index()
        result.columns = ['Start', 'End', 'MIDI']
        return result
    
    @staticmethod
    def _get_lowest_midi(dataframe):
        dataframe['MIDI'] = dataframe['MIDI'].apply(lambda x: min(x) if x else None)
        dataframe = dataframe.dropna(subset=['MIDI'])
        return dataframe[['Start', 'End', 'MIDI']]
    
    @staticmethod
    def _combine_consecutive_midi_values(dataframe):
        result = []
        current_start = None
        current_end = None
        current_midi = None
        for _, row in dataframe.iterrows():
            if current_midi == row['MIDI']:
                current_end = row['End']
            else:
                if current_midi is not None:
                    result.append([current_start, current_end, current_midi])
                current_start = row['Start']
                current_end = row['End']
                current_midi = row['MIDI']
        result.append([current_start, current_end, current_midi])
        return pandas.DataFrame(result, columns=['Start', 'End', 'MIDI'])
    
    @staticmethod
    def _is_prime(num):
        if num < 2:
            return False
        for i in range(2, num):
            if num % i == 0:
                return False
        return True
    
    @functools.lru_cache()
    def _get_factors(self, num):
        factors = []
        i = 1
        while i <= num:
            if num % i == 0:
                factors.append(i)
            i += 1
        return factors
    
    # Include start and end data in dataframe so that you can aggregate repeated notes in bass part
class Percussion(Part):
    def __init__(self, sivs, grid=None, midi=None):
        super().__init__(sivs, grid, midi)
        self.name = 'Percussion'
        
    def create_part(self):
        notes_data = []
        for i in range(len(self.bin)):
            midi_pool = itertools.cycle(self._midi_pool(i))
            for j in range(len(self.factors)):
                pattern = numpy.tile(self.bin[i], self.factors[j])
                indices = numpy.nonzero(pattern)[0]
                dur = self.grid * (self.period / self.factors[j])
                for k in indices:
                    offset = k * dur
                    notes_data.append([offset, offset + self.grid, next(midi_pool)])
        notes_data = [[round(data[0], 6), round(data[1], 6), data[2]] for data in notes_data]
        self.dataframe = pandas.DataFrame(notes_data, columns=['Start', 'End', 'MIDI']).sort_values(by = 'Start').drop_duplicates()
        Utility.save_as_csv(self.dataframe, f'part {self.id}')
        
    def _midi_pool(self, index):
        events = self.bin[index].count(1)
        largest_prime_slice = slice(0, self._get_largest_prime_factor(events))
        instrument_pool = itertools.cycle(self.midi[largest_prime_slice])
        return [next(instrument_pool) for _ in range(events)]
    
class Bass(Part):
    def __init__(self, sivs, grid=None, midi=None):
        super().__init__(sivs, grid, midi)
        self.name = 'Bass'
        
    def create_part(self):
        notes_data = []
        for i in range(len(self.bin)):
            midi_pool = itertools.cycle(self._midi_pool(i))
            for j in range(len(self.factors)):
                pattern = numpy.tile(self.bin[i], self.factors[j])
                indices = numpy.nonzero(pattern)[0]
                dur = self.grid * (self.period / self.factors[j])
                for k in indices:
                    offset = k * dur
                    notes_data.append([offset, offset + self.grid, next(midi_pool)])
        notes_data = [[round(data[0], 6), round(data[1], 6), data[2]] for data in notes_data]
        self.dataframe = pandas.DataFrame(notes_data, columns=['Start', 'End', 'MIDI']).sort_values(by = 'Start').drop_duplicates()
        self.dataframe = self._grouped_by_start(self.dataframe)
        self.dataframe = self._get_lowest_midi(self.dataframe)
        self.dataframe = self._combine_consecutive_midi_values(self.dataframe)
        Utility.save_as_csv(self.dataframe, f'part {self.id}')
        
    def _midi_pool(self, index):
        pitch_class = self._octave_interpolation(self.intervals)
        tonality = 40
        pool = [pitch + tonality for pitch in pitch_class[index]]
        return pool
    
# Map intervals onto mod-12 semitones, then map again on those intervals to create chords.
class Keyboard(Part):
    def __init__(self, sivs, grid=None, midi=None):
        super().__init__(sivs, grid, midi)
        self.name = 'Keyboard'
        
    def create_part(self):
        notes_data = []
        for i in range(len(self.bin)):
            midi_pool = itertools.cycle(self._midi_pool(i))
            for j in range(len(self.factors)):
                pattern = numpy.tile(self.bin[i], self.factors[j])
                indices = numpy.nonzero(pattern)[0]
                dur = self.grid * (self.period / self.factors[j])
                for k in indices:
                    offset = k * dur
                    notes_data.append([offset, offset + self.grid, next(midi_pool)])
        notes_data = [[round(data[0], 6), round(data[1], 6), data[2]] for data in notes_data]
        self.dataframe = pandas.DataFrame(notes_data, columns=['Start', 'End', 'MIDI']).sort_values(by = 'Start').drop_duplicates()
        
    def _midi_pool(self, index):
        pitch_class = self._octave_interpolation(self.intervals)
        tonality = 40
        pool = [pitch + tonality for pitch in pitch_class[index]]
        return pool
    
class Utility:
    def grouped_by_offset_and_midi(dataframe):
        grouped_by_offset = dataframe.groupby('Offset')['MIDI'].apply(lambda x: sorted([i for i in x])).reset_index()
        grouped_by_offset['MIDI'] = grouped_by_offset['MIDI'].apply(tuple)
        return grouped_by_offset.groupby('MIDI')['Start'].agg(lambda x: list(x)).reset_index()
    
    def aggregate_rows(dataframe):
        groups = dataframe.groupby('MIDI')
        result = pandas.DataFrame(columns=['Start', 'End', 'MIDI'])
        for name, group in groups:
            start = group['Start'].iloc[0]
            end = group['End'].iloc[-1] if group['End'].iloc[-1] is not pandas.NA else group['Start'].iloc[-1] + 1
            result = result.append({'Start': start, 'End': end, 'MIDI': name}, ignore_index=True)
        return result
    
    @staticmethod
    def save_as_csv(dataframe, filename):
        dataframe.sort_values(by = 'Start').to_csv(f'sifters/.{filename}.csv', index=False)
        
    @staticmethod
    def save_as_midi(pretty_midi_obj, filename):
        pretty_midi_obj.write(f'sifters/.{filename}.mid')
        
if __name__ == '__main__':
    sivs = '((8@0|8@1|8@7)&(5@1|5@3))', '((8@0|8@1|8@2)&5@0)', '((8@5|8@6)&(5@2|5@3|5@4))', '(8@6&5@1)', '(8@3)', '(8@4)', '(8@1&5@2)'
    # perc1 = Percussion(sivs)
    # perc2 = Percussion(sivs, '4/3')
    bass1 = Bass(sivs)
    score = Score(bass1)
    score = score.create_score()
    Utility.save_as_midi(score, 'score')
    # print(Utility.aggregate_rows(bass1.dataframe))