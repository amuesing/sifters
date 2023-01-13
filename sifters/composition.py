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
    
    @staticmethod
    def get_binary(sivs):
        bin = []
        if isinstance(sivs, tuple):
            per = []
            obj = []
            for siv in sivs:
                objects = music21.sieve.Sieve(siv)
                obj.append(objects)
                per.append(objects.period())
            lcm = numpy.lcm.reduce(per)
            for o in obj:
                o.setZRange(0, lcm - 1)
                bin.append(o.segment(segmentFormat='binary'))
        else:
            obj = music21.sieve.Sieve(sivs)
            obj.setZRange(0, obj.period() - 1)
            bin.append(obj.segment(segmentFormat='binary'))
        return bin
    
    @staticmethod
    def get_intervals(sivs):
        intervals = []
        for siv in sivs:
            set = music21.sieve.Sieve(siv)
            set.setZRange(0, set.period() - 1)
            intervals.append(set.segment())
        return intervals
    
    @staticmethod
    def get_factors(num):
        factors = []
        i = 1
        while i <= num:
            if num % i == 0:
                factors.append(i)
            i += 1
        return factors
    
    @staticmethod
    def get_largest_prime_factor(num):
        for i in range(num, 1, -1):
            if num % i == 0 and all(i % j for j in range(2, i)):
                return i
        return 1
    
    @staticmethod
    def get_least_common_multiple(numbers):
        lcm = numbers[0]
        for i in range(1, len(numbers)):
            lcm = lcm * numbers[i] // math.gcd(lcm, numbers[i])
        return lcm
        
    # @staticmethod
    # def get_least_common_multiple(a, b):
    #     return (a * b) // math.gcd(a, b)
        
class Percussion(Composition):
    grid_history = []
    next_id = 0
    
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
        for b in self.bin:
            midi_pool = itertools.cycle(self.midi_pool(b))
            for i in range(len(self.factors)):
                pattern = (b * self.factors[i]) 
                dur = self.grid * (self.period / self.factors[i])
                part = music21.stream.Part()
                for j, bit in enumerate(pattern):
                    if bit == 1:
                        note = music21.note.Note(midi=next(midi_pool), quarterLength=self.grid)
                        part.insert(j * dur, note)
                self.stream.insert(0, part)
                
    def midi_pool(self, bin):
        events = bin.count(1)
        lpf_slice = slice(0, self.get_largest_prime_factor(events))
        instrument_pool = itertools.cycle([60,61,62,63,64][lpf_slice])
        return [next(instrument_pool) for _ in range(events)]
    
    def construct_part(self):
        Composition.construct_part(self, self.stream)

class Score():
    normalized_numerators = []
    normalized_denominators = []
    multipliers = []
    
    def __init__(self, *args):
        self.args = args
    
    @staticmethod
    def get_multiplier(arg):
        lcd = functools.reduce(math.lcm, (fraction.denominator for fraction in arg.grid_history))
        return [lcd // fraction.denominator for fraction in arg.grid_history][arg.id]
    
    @staticmethod
    def normalize_numerator(arg, mult):
        return arg.grid_history[arg.id].numerator * mult
    
    @staticmethod
    def normalize_denominator(arg, mult):
        # Score.normalized_numerators.append(mult * arg.grid_history[arg.id].numerator)
        return arg.grid_history[arg.id].denominator * mult

    @staticmethod
    def generate_dataframe(arg):
        parts = arg.stream.parts
        rows_list = []
        for part in parts:
            for elt in part.getElementsByClass([music21.note.Note]):
                d = {'Offset': elt.offset}
                if hasattr(elt, 'pitches'):
                    d.update({'Midi': pitch.midi for pitch in elt.pitches})
                rows_list.append(d)
        return pandas.DataFrame(rows_list).drop_duplicates()
    
    @staticmethod
    def duplicate_dataframe(arg, df, n):
        frames = [df]
        delta = 0
        for _ in range(1, n):
            df["Offset"] += delta * arg.grid_history[arg.id]
            frames.append(df)
            print(delta * arg.grid_history[arg.id])
            delta += math.pow(arg.period, 2)
        return pandas.concat(frames)
        
    @staticmethod
    def csv_to_midi(dataframe, arg):
        part = music21.stream.Part()
        result = {}
        for _, row in dataframe.iterrows():
            offset = row['Offset']
            mid = int(row['Midi'])
            result[offset] = result.get(offset, []) + [mid]
        for offset, mid in result.items():
            notes = [music21.note.Note(m, quarterLength=arg.grid) for m in mid] 
            part.insert(offset, music21.chord.Chord(notes) if len(notes) > 1 else notes[0])
        return part.makeRests(fillGaps=True)
    
    @staticmethod
    def set_measure_zero(score, arg, part_num):
        score.insert(0, music21.meter.TimeSignature('5/4'))
        if arg.name == 'Percussion':
            score.insert(0, music21.instrument.UnpitchedPercussion())
            score.insert(0, music21.clef.PercussionClef())
        if arg.name == 'Bass':
            score.insert(0, music21.instrument.Bass())
            score.insert(0, music21.clef.BassClef())
        if arg.name == 'Keyboard':
            score.insert(0, music21.instrument.Piano())
            score.insert(0, music21.clef.TrebleClef())
        if part_num == 1:
            score.insert(0, music21.tempo.MetronomeMark('fast', 144, music21.note.Note(type='quarter')))
        return score
    
    def construct_score(self):
        score = music21.stream.Score()
        score.insert(0, music21.metadata.Metadata())
        score.metadata.title = 'Sifters'
        score.metadata.composer = 'Ari Müsing'
        part_num = 1
        for arg in self.args:
            mult = self.get_multiplier(arg)
            self.normalized_numerators.append(self.normalize_numerator(arg, mult))
            self.normalized_denominators.append(self.normalize_denominator(arg, mult))
        lcm = arg.get_least_common_multiple(self.normalized_numerators)
        for arg in self.args:
            self.multipliers.append(lcm // self.normalized_numerators[arg.id])
        for arg in self.args:
            print(f'Constructing {arg.name} Part')
            df = self.generate_dataframe(arg)
            # dup = self.duplicate_dataframe(arg, df, self.multipliers[arg.id])
            form = self.csv_to_midi(df, arg)
            comp = self.set_measure_zero(form, arg, part_num)
            comp.write('midi', f'sifters/data/midi/.{arg.name}_{arg.id}.mid')
            sorted = df.sort_values(by = 'Offset')
            sorted.to_csv(f'sifters/data/csv/.{arg.name}_{arg.id}.csv', index=False)
            score.insert(0, comp)
            part_num += 1
        return score
        
if __name__ == '__main__':
    sivs = '((8@0|8@1|8@7)&(5@1|5@3))', '((8@0|8@1|8@2)&5@0)', '((8@5|8@6)&(5@2|5@3|5@4))', '(8@6&5@1)', '(8@3)', '(8@4)', '(8@1&5@2)'
    perc1 = Percussion(sivs)
    perc2 = Percussion(sivs, '2/3')
    perc3 = Percussion(sivs, '6/5')
    score = Score(perc1, perc2, perc3)
    score = score.construct_score()