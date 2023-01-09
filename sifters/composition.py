import music21
import numpy
import itertools
import pandas

class Composition:
    def __init__(self, sivs):
        self.intervals = self.get_intervals(sivs)
        self.bin = self.get_binary(sivs)
        self.period = len(self.bin[0])
        self.factors = self.get_factors(self.period)
        self.voices = len(self.factors)
        self.grid = 0.5
    
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
        if a > b:
            greater = a
        else:
            greater = b
        while(True):
            if((greater % a == 0) and (greater % b == 0)):
                lcm = greater
                break
            greater += 1
        return lcm
        
class Percussion(Composition):
    def __init__(self, sivs):
        super().__init__(sivs)
        self.stream = music21.stream.Score()
        self.name = 'Percussion'
        self.create_notes()
        
    def create_notes(self):
        for b in self.bin:
            midi_pool = itertools.cycle(self.midi_pool(b))
            for i in range(self.voices):
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
        
class Bass(Composition):
    def __init__(self, sivs):
        super().__init__(sivs)
        self.stream = music21.stream.Score()
        self.name = 'Bass'
        self.ratio = 1 + 1/3
        self.inner_grid = self.grid * self.ratio
        self.inner_period = self.period / self.ratio
        self.create_parts()
        
    # def create_notes(self):
    #     for i, b in enumerate(self.bin):
    #         part = music21.stream.Part()
    #         pattern = b * int(self.inner_period)
    #         midi_pool = itertools.cycle(self.midi_pool(i))
    #         for i, bit in enumerate(pattern):
    #             if bit == 1:
    #                 note = music21.note.Note(midi=next(midi_pool), quarterLength=self.inner_grid)
    #                 part.insert(i * self.inner_grid, note)
    #         self.stream.insert(0, part)
        
    def create_parts(self):
        for _ in range(self.voices):
            for i, b in enumerate(self.bin):
                self.stream.insert(0, self.create_notes(i, b))
            
    def create_notes(self, index, bin):
        part = music21.stream.Part()
        pattern = bin * int(self.inner_period)
        midi_pool = itertools.cycle(self.midi_pool(index))
        for i, bit in enumerate(pattern):
            if bit == 1:
                part.insert(i * self.inner_grid, music21.note.Note(midi=next(midi_pool), quarterLength=self.inner_grid))
        return part
    
    def midi_pool(self, index):
        tonality = 40
        pool = [inter + tonality for inter in self.intervals[index]]
        return pool
    
    def construct_part(self):
        Composition.construct_part(self, self.stream)
        
class Keyboard(Composition):
    def __init__(self, sivs):
        super().__init__(sivs)
        self.stream = music21.stream.Score()
        self.name = 'Keyboard'
        self.create_parts()
        
    def create_parts(self):
        parts = []
        for i in range(self.voices):
            index = 0
            p = music21.stream.Stream()
            for b in self.bin:
                p.insert(0, self.create_notes(b, self.factors[i], index))
                index += 1
            for notes in p:
                parts.insert(0, notes)
        for p in parts:
            self.stream.insert(0, p)
            
    def create_notes(self, bin, factor, index):
        part = music21.stream.Part()
        pattern = (bin * factor) * 4
        dur = self.grid * (self.period / factor)
        events = self.midi_pool(bin, index)
        midi_pool = itertools.cycle(events)
        for i, bit in enumerate(pattern):
            if bit == 1:
                part.insert(i * dur, music21.note.Note(midi=next(midi_pool), quarterLength=self.grid))
        return part
    
    def midi_pool(self, bin, index):
        events = bin.count(1)
        notes = [[i + 60 for i in inter] for inter in self.intervals]
        lpf_slice = slice(0, self.get_largest_prime_factor(events))
        instrument_pool = itertools.cycle(notes[index]) 
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
        # score.insert(0, music21.meter.TimeSignature('5/4'))
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
            comp.write('midi', f'sifters/data/midi/{arg.name}.mid')
            sorted = df.sort_values(by = 'Offset')
            sorted.to_csv(f'sifters/data/csv/{arg.name}.csv', index=False)
            score.insert(0, comp)
            part_num += 1
        return score
        
if __name__ == '__main__':
    sivs = '((8@0|8@1|8@7)&(5@1|5@3))', '((8@0|8@1|8@2)&5@0)', '((8@5|8@6)&(5@2|5@3|5@4))', '(8@6&5@1)', '(8@3)', '(8@4)', '(8@1&5@2)'
    perc = Percussion(sivs)
    bass = Bass(sivs)
    # keys = Keyboard(sivs)
    score = Score(perc, bass)
    score = score.construct_score()
    score.show()