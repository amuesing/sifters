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
    def get_least_common_multiple(a, b):
        return (a * b) // math.gcd(a, b)
    
    @staticmethod
    def get_least_common_denominator(grid_history):
        denominators = [fraction.denominator for fraction in grid_history]
        return functools.reduce(lambda a, b: a*b // math.gcd(a, b), denominators)
        # lcm = functools.reduce(lambda a, b: a*b // math.gcd(a, b), denominators)
        # return [lcm // fraction.denominator for fraction in grid_history]
        
class Percussion(Composition):
    grid_history = []
    def __init__(self, sivs, grid=None):
        super().__init__(sivs)
        self.stream = music21.stream.Score()
        self.name = 'Percussion'
        self.grid = fractions.Fraction(grid) if grid is not None else self.grid
        self.grid_history.append(self.grid)
        self.create_notes()
        
    def test(self):
        lcd = Composition.get_least_common_denominator(self.grid_history)
        return [lcd // fraction.denominator for fraction in perc1.grid_history]
        
    def create_notes(self):
        for b in self.bin:
            midi_pool = itertools.cycle(self.midi_pool(b))
            for i in range(len(self.factors)):
                pattern = b * self.factors[i]
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
    def __init__(self, *args):
        self.args = args
        
    @staticmethod
    def generate_dataframe(score):
        parts = score.parts
        rows_list = []
        for part in parts:
            for elt in part.getElementsByClass([music21.note.Note]):
                d = {'Offset': elt.offset}
                if hasattr(elt, 'pitches'):
                    d.update({'Midi': pitch.midi for pitch in elt.pitches})
                rows_list.append(d)
        return pandas.DataFrame(rows_list).drop_duplicates()
    
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
            print(f'Constructing {arg.name} Part')
            df = self.generate_dataframe(arg.stream)
            form = self.csv_to_midi(df, arg)
            comp = self.set_measure_zero(form, arg, part_num)
            comp.write('midi', f'sifters/data/midi/.{arg.name}.mid')
            sorted = df.sort_values(by = 'Offset')
            sorted.to_csv(f'sifters/data/csv/.{arg.name}.csv', index=False)
            score.insert(0, comp)
            lcm = functools.reduce(math.lcm, (fraction.denominator for fraction in arg.grid_history))
            part_num += 1
        return score
        
if __name__ == '__main__':
    sivs = '((8@0|8@1|8@7)&(5@1|5@3))', '((8@0|8@1|8@2)&5@0)', '((8@5|8@6)&(5@2|5@3|5@4))', '(8@6&5@1)', '(8@3)', '(8@4)', '(8@1&5@2)'
    perc1 = Percussion(sivs)
    perc2 = Percussion(sivs, ('2/3'))
    perc3 = Percussion(sivs, '6/5')
    score = Score(perc1, perc2, perc3)
    score = score.construct_score()
    # lcd = Composition.get_least_common_denominator(perc1.grid_history)
    # print([lcd // fraction.denominator for fraction in perc1.grid_history])
    # print(perc1.grid_history)
    print(perc1.test())