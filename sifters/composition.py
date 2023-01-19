import music21
import numpy
import itertools
import pandas
import fractions
import math
import functools

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
    
    @staticmethod
    def get_least_common_multiple(numbers):
        lcm = numbers[0]
        for i in range(1, len(numbers)):
            lcm = lcm * numbers[i] // math.gcd(lcm, numbers[i])
        return lcm

class Percussion(Composition):
    grid_history = []
    next_id = 1
    
    def __init__(self, sivs, grid=None):
        super().__init__(sivs)
        self.stream = music21.stream.Score()
        self.name = 'Percussion'
        self.grid = fractions.Fraction(grid) if grid is not None else self.grid
        self.grid_history.append(self.grid)
        self.id = Percussion.next_id
        Percussion.next_id += 1
        self.create_notes()
        
    def create_notes(self):
        for i, _ in enumerate(self.bin):
            midi_pool = itertools.cycle(self.midi_pool(i))
            for j in range(len(self.factors)):
                pattern = self.bin[i] * self.factors[j]
                indices = numpy.nonzero(pattern)[0]
                dur = self.grid * (self.period / self.factors[j])
                # anytime I am using a part to hold values it may be more efficient to save within a dataframe
                part = music21.stream.Part()
                for k in indices:
                    note = music21.note.Note(midi=next(midi_pool), quarterLength=self.grid)
                    part.insert(k * dur, note)
                self.stream.insert(0, part)
                
    def midi_pool(self, index):
        events = self.bin[index].count(1)
        largest_prime_slice = slice(0, self.get_largest_prime_factor(events))
        instrument_pool = itertools.cycle([60,61,62,63,64][largest_prime_slice])
        return [next(instrument_pool) for _ in range(events)]

class Score():
    def __init__(self, *args):
        self.args = args
        self.normalized_numerators = []
        self.normalized_denominators = []
        self.multipliers = []
    
    @staticmethod
    def get_multiplier(arg):
        lcd = functools.reduce(math.lcm, (fraction.denominator for fraction in arg.grid_history))
        return [lcd // fraction.denominator for fraction in arg.grid_history][arg.id-1]
    
    @staticmethod
    @functools.lru_cache()
    def normalize_numerator(arg, mult):
        return arg.grid_history[arg.id-1].numerator * mult
    
    @staticmethod
    @functools.lru_cache()
    def normalize_denominator(arg, mult):
        return arg.grid_history[arg.id-1].denominator * mult
    
    @staticmethod
    @functools.lru_cache()
    def generate_dataframe(arg):
        parts = arg.stream.parts
        rows_list = []
        for part in parts:
            for elt in part.getElementsByClass([music21.note.Note]):
                d = {'Offset': float(elt.offset)}
                if hasattr(elt, 'pitches'):
                    d.update({'Midi': pitch.midi for pitch in elt.pitches})
                rows_list.append(d)
        return pandas.DataFrame(rows_list).drop_duplicates()
    
    @staticmethod
    def normalize_periodicity(arg, df, num):
        duplicates = [df.copy()]
        inner_period = math.pow(arg.period, 2)
        for i in range(num):
            df_copy = df.copy()
            df_copy['Offset'] = df_copy['Offset'] + (inner_period * arg.grid) * i
            duplicates.append(df_copy)
        result = pandas.concat(duplicates)
        return result.drop_duplicates()
    
    @staticmethod
    def csv_to_midi(dataframe, arg):
        part = music21.stream.Part()
        result = {}
        for _, row in dataframe.iterrows():
            offset = row['Offset']
            mid = int(row['Midi'])
            result.setdefault(offset, []).append(mid)
        for offset, mid in result.items():
            notes = [music21.note.Note(m, quarterLength=arg.grid) for m in mid] 
            part.insert(offset, music21.chord.Chord(notes) if len(notes) > 1 else notes[0])
        return part.makeRests(fillGaps=True)
    
    @staticmethod
    def set_measure_zero(score, arg, part_num):
        score.insert(0, music21.meter.TimeSignature('5/4'))
        instruments_clefs = {
            'Percussion': (music21.instrument.UnpitchedPercussion(), music21.clef.PercussionClef()),
            'Bass': (music21.instrument.Bass(), music21.clef.BassClef()),
            'Keyboard': (music21.instrument.Piano(), music21.clef.TrebleClef())
        }
        score.insert(0, instruments_clefs[arg.name][0])
        score.insert(0, instruments_clefs[arg.name][1])
        if part_num == 1:
            score.insert(0, music21.tempo.MetronomeMark('fast', 112, music21.note.Note(type='half')))
        return score
    
    def construct_score(self):
        score = music21.stream.Score()
        score.insert(0, music21.metadata.Metadata())
        score.metadata.title = 'Sifters'
        score.metadata.composer = 'Aaron Muesing'
        part_num = 1
        for arg in self.args:
            mult = self.get_multiplier(arg)
            self.normalized_numerators.append(self.normalize_numerator(arg, mult))
            self.normalized_denominators.append(self.normalize_denominator(arg, mult))
        lcm = arg.get_least_common_multiple(self.normalized_numerators)
        for arg in self.args:
            self.multipliers.append(lcm // self.normalized_numerators[arg.id-1])
        for arg in self.args:
            print(f'Constructing {arg.name} {arg.id} Part')
            df = self.generate_dataframe(arg)
            norm = self.normalize_periodicity(arg, df, self.multipliers[arg.id-1])
            form = self.csv_to_midi(norm, arg)
            comp = self.set_measure_zero(form, arg, part_num)
            score.insert(0, comp)
            part_num += 1
        return score
        
if __name__ == '__main__':
    sivs = '((8@0|8@1|8@7)&(5@1|5@3))', '((8@0|8@1|8@2)&5@0)', '((8@5|8@6)&(5@2|5@3|5@4))', '(8@6&5@1)', '(8@3)', '(8@4)', '(8@1&5@2)'
    siv = '((8@5|8@6)&(5@2|5@3|5@4))', '(8@6&5@1)'
    perc1 = Percussion(sivs)
    # perc2 = Percussion(sivs, '2/3')
    # bass1 = Bass(siv, '5/3')
    # bass2 = Bass(siv, '4/5')
    # perc2 = Percussion(sivs, '2/3')
    # perc3 = Percussion(sivs, '6/5')
    score = Score(perc1)
    score = score.construct_score()
    # score.show('midi')
    score.show()