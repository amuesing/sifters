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
            
    # data is generated in Part class, and manipulated in Score class. Utility class holds methods used outside of the code's core functionality
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
                print(f'Constructing {arg.id} Part')
                norm = self._normalize_periodicity(arg, multiplier)
                notes = self._csv_to_midi(norm, arg)
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
            df_copy['Offset'] = df_copy['Offset'] + (length_of_one_rep * arg.grid) * i
            df_copy['MIDI'] = df_copy['MIDI'] + i
            duplicates.append(df_copy)
        result = pandas.concat(duplicates)
        result = result.drop_duplicates()
        Utility.save_as_csv(result, f'norm {arg.name} {arg.id}')
        group = Utility.grouped_by_offset(result)
        Utility.save_as_csv(group, f'grouped norm {arg.name} {arg.id}')
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
    def _csv_to_midi(dataframe, arg):
        dataframe = dataframe.groupby('MIDI', group_keys=True).apply(lambda x: x.assign(start=x.Offset, end=x.Offset + arg.grid))
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
    
class Percussion(Part):
    def __init__(self, sivs, grid=None, midi=None):
        super().__init__(sivs, grid)
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
                    notes_data.append([k*dur, next(midi_pool)])
        notes_data = [[round(x[0], 6), x[1]] for x in notes_data]
        self.dataframe = pandas.DataFrame(notes_data, columns=['Offset', 'MIDI']).sort_values(by = 'Offset').drop_duplicates()
        
    def _midi_pool(self, index):
        events = self.bin[index].count(1)
        largest_prime_slice = slice(0, self._get_largest_prime_factor(events))
        instrument_pool = itertools.cycle(self.midi[largest_prime_slice])
        return [next(instrument_pool) for _ in range(events)]
    
class Utility:
    @staticmethod
    # this method first groups all midi notes that share the same offset value, then groups all of the offset values that share that group of midi notes
    def grouped_by_offset(dataframe):
        return dataframe.groupby('Offset')['MIDI'].apply(lambda x: sorted([i for i in x])).reset_index()
    
    def grouped_by_offset_and_midi(dataframe):
        grouped_by_offset = dataframe.groupby('Offset')['MIDI'].apply(lambda x: sorted([i for i in x])).reset_index()
        grouped_by_offset['MIDI'] = grouped_by_offset['MIDI'].apply(tuple)
        return grouped_by_offset.groupby('MIDI')['Offset'].agg(lambda x: list(x)).reset_index()
    
    @staticmethod
    def save_as_csv(dataframe, filename):
        dataframe.sort_values(by = 'Offset').to_csv(f'sifters/data/csv/.{filename}.csv', index=False)
        
    @staticmethod
    def save_as_midi(pretty_midi_obj, filename):
        pretty_midi_obj.write(f'sifters/data/midi/.{filename}.mid')
        
if __name__ == '__main__':
    sivs = '((8@0|8@1|8@7)&(5@1|5@3))', '((8@0|8@1|8@2)&5@0)', '((8@5|8@6)&(5@2|5@3|5@4))', '(8@6&5@1)', '(8@3)', '(8@4)', '(8@1&5@2)'
    perc1 = Percussion(sivs, '15/15')
    perc2 = Percussion(sivs, '12/15')
    perc3 = Percussion(sivs, '10/15')
    # perc1 = Percussion(sivs)
    # perc2 = Percussion(sivs, '2/3')
    # perc3 = Part(sivs, 'Percussion', '3/4')
    # score = Score(perc1, perc2, perc3)
    score = Score(perc1, perc2, perc3)
    score.create_score()
    
    def distribute_grid(*args, multipliers):
        normalized_grid = []
        for arg, multiplier in zip(args, multipliers):
            total = arg.grid.numerator * multiplier
            combinations = find_combinations(range(total), total, multiplier)
            # print(arg.grid)
            # print(f'combinations: {combinations}')
            # print(f'range: {range(total)}')
            # print(f'total: {total}')
            # print(f'mult: {multiplier}')
            min_range_tuple = find_min_range_tuple(combinations)
            # print(min_range_tuple)
            lcd = find_least_common_denominator(arg)
            normalize_fractions(arg, lcd, multiplier)
        #     normalized_grid.append((distribute_numerator(arg, min_range_tuple)))
        # return normalized_grid
        
    def find_least_common_denominator(arg):
        lcd = 1
        for frac in arg.grid_history:
            lcd = math.lcm(lcd, frac.denominator)
        return lcd
        
    def normalize_fractions(arg, lcd, mult):
        m = lcd // arg.grid.denominator
        print((arg.grid.numerator * m) * mult)
        # print(mult * arg.grid.numerator)
        # print(m)
        
    
    # def find_combinations(numbers, total, length):
    #     # Find all combinations of the given length within the set of numbers
    #     combinations = [c for c in itertools.combinations_with_replacement(numbers, length)]
    #     # Filter the combinations that add up to the given total and that don't contain 0
    #     return [c for c in combinations if sum(c) == total and 0 not in c]
    
    def find_combinations(numbers, total, length):
        # Find all combinations of the given length within the set of numbers
        combinations = [c for c in itertools.combinations(numbers, length)]
        # Filter the combinations that add up to the given total and that don't contain 0
        return [c for c in combinations if sum(c) == total and 0 not in c]
    
    def find_min_range_tuple(tuples):
        min_range = float("inf")
        min_tuple = None
        for tup in tuples:
            range = max(tup) - min(tup)
            if range < min_range:
                min_range = range
                min_tuple = tup
        return min_tuple
    
    def distribute_numerator(arg, tuple):
        normalized_fractions = []
        for num in tuple:
            normalized_fractions.append(fractions.Fraction(num, arg.grid.denominator))
        return normalized_fractions
    
    def create_distributed_segment(distributed_grid):
        parts = []
        for part in distributed_grid:
            segment = []
            for grid in part:
                perc = Percussion(sivs=sivs, grid=grid)
                segment.append(perc)
            parts.append(segment)
        return parts
    
    def combine_segments(parts):
        offset_history = []
        for part in parts:
            offset = []
            for i, segment in enumerate(part):
                length_of_one_rep = math.pow(segment.period, 2)
                # print(segment.dataframe['Offset'] + (length_of_one_rep * segment.grid) * i)
                offset.append((length_of_one_rep * segment.grid) * i)
            offset_history.append(offset)
        return offset_history
                    
    distributed = distribute_grid(perc1, perc2, perc3, multipliers=score.multipliers)
    # parts = create_distributed_segment(distributed)
    # df = parts[0][3].dataframe
    # print(combine_segments(parts))