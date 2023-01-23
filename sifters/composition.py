import music21
import pretty_midi
import fractions
import itertools
import functools
import pandas
import numpy
import math

class Composition:
    def __init__(self, sivs):
        self.intervals = self.get_intervals(sivs)
        self.bin = self.get_binary(sivs)
        self.period = len(self.bin[0])
        self.factors = self.get_factors(self.period)
        self.grid = fractions.Fraction(1, 1)
        
    @functools.lru_cache()
    def get_binary(self, sivs):
        bin = []
        if isinstance(sivs, tuple):
            per = []
            obj = []
            for siv in sivs:
                objects = music21.sieve.Sieve(siv)
                obj.append(objects)
                per.append(objects.period())
            lcm = self.get_least_common_multiple(per)
            for o in obj:
                o.setZRange(0, lcm - 1)
                bin.append(o.segment(segmentFormat='binary'))
        else:
            obj = music21.sieve.Sieve(sivs)
            obj.setZRange(0, obj.period() - 1)
            bin.append(obj.segment(segmentFormat='binary'))
        return bin
    
    @functools.lru_cache()
    def get_intervals(self, sivs):
        intervals = []
        for siv in sivs:
            set = music21.sieve.Sieve(siv)
            set.setZRange(0, set.period() - 1)
            intervals.append(set.segment())
        return intervals
    
    @functools.lru_cache()
    def get_factors(self, num):
        factors = []
        i = 1
        while i <= num:
            if num % i == 0:
                factors.append(i)
            i += 1
        return factors
    
    @staticmethod
    def is_prime(num):
        if num < 2:
            return False
        for i in range(2, num):
            if num % i == 0:
                return False
        return True
    
    @staticmethod
    def get_largest_prime_factor(num):
        for i in range(1, int(num ** 0.5) + 1):
            if num % i == 0:
                factor = num // i
                if Composition.is_prime(factor):
                    return factor
                elif Composition.is_prime(i):
                    return i
        return num
    
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
        
class Part(Composition):
    grid_history = []
    next_id = 1
    
    def __init__(self, sivs, name, grid=None):
        super().__init__(sivs)
        self.name = name
        self.grid = fractions.Fraction(grid) if grid is not None else self.grid
        self.grid_history.append(self.grid)
        self.id = Part.next_id
        Part.next_id += 1
        
    def create_notes(self):
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
        largest_prime_slice = slice(0, self.get_largest_prime_factor(events))
        instrument_pool = itertools.cycle([45, 46, 47, 48, 49][largest_prime_slice])
        return [next(instrument_pool) for _ in range(events)]
    
class Score:
    def __init__(self, *args):
        self.args = args
        self.normalized_numerators = []
        self.normalized_denominators = []
        self.multipliers = []
    
    def construct_score(self):
        score = pretty_midi.PrettyMIDI()
        score.time_signature_changes.append(pretty_midi.TimeSignature(5,4,0))
        score.resolution = 440
        self.normalized_numerators = numpy.array([self._normalize_numerator(arg, self._get_multiplier(arg)) for arg in self.args])
        lcm = self.args[-1].get_least_common_multiple(self.normalized_numerators)
        self.multipliers = lcm // self.normalized_numerators
        notes_list = []
        #move instrument object to Part class
        instruments = []
        for arg, multiplier in zip(self.args, self.multipliers):
                print(f'Constructing {arg.name} {arg.id} Composition')
                norm = self._normalize_periodicity(arg, multiplier)
                norm.sort_values(by = 'Offset').to_csv(f'sifters/data/csv/.{arg.name}_{arg.id}.csv', index=False)
                notes = self._csv_to_midi(norm, arg)
                notes_list.append(notes)
                instruments.append(pretty_midi.Instrument(program=0, name=arg.name))
        for i,arg in enumerate(self.args):
            instruments[i].notes = notes_list[i]
            score.instruments.append(instruments[i])
        print('Build Complete')
        return score
    
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
    def _normalize_periodicity(arg, num):
        arg.create_notes()
        duplicates = [arg.dataframe.copy()]
        inner_period = math.pow(arg.period, 2)
        for i in range(num):
            df_copy = arg.dataframe.copy()
            df_copy['Offset'] = df_copy['Offset'] + (inner_period * arg.grid) * i
            duplicates.append(df_copy)
        result = pandas.concat(duplicates)
        return result.drop_duplicates()
    
    @staticmethod
    def _csv_to_midi(dataframe, arg):
        dataframe = dataframe.groupby('MIDI', group_keys=True).apply(lambda x: x.assign(start=x.Offset, end=x.Offset + arg.grid))
        return [pretty_midi.Note(velocity=100, pitch=int(row['MIDI']), start=row['start'], end=row['end']) for _, row in dataframe.iterrows()]
    

if __name__ == '__main__':
    sivs = '((8@0|8@1|8@7)&(5@1|5@3))', '((8@0|8@1|8@2)&5@0)', '((8@5|8@6)&(5@2|5@3|5@4))', '(8@6&5@1)', '(8@3)', '(8@4)', '(8@1&5@2)'
    perc1 = Part(sivs, 'Percussion', '4/3')
    # perc2 = Instrument(sivs, '3/4')
    # perc3 = Instrument(sivs, '4/5')
    score = Score(perc1)
    score = score.construct_score()
    # write a method to convert midi to musicxml file
    score.write('sifters/data/midi/.score.mid')
    
