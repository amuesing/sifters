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
        self.grid = 1
    
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
    
    def csv_to_midi(self, dataframe):
        part = music21.stream.Score()
        result = {}
        for _, row in dataframe.iterrows():
            offset = row['Offset']
            mid = int(row['Midi'])
            result[offset] = result.get(offset, []) + [mid]
        for offset, mid in result.items():
            notes = [music21.note.Note(m, quarterLength=self.grid) for m in mid]
            part.insert(offset, music21.chord.Chord(notes) if len(notes) > 1 else notes[0])
        return part.makeRests(fillGaps=True)
    
    @staticmethod
    def set_measure_zero(score):
        score.insert(0, music21.metadata.Metadata())
        score.metadata.title = 'Sifters'
        score.metadata.composer = 'Ari Müsing'
        score.insert(0, music21.instrument.UnpitchedPercussion())
        score.insert(0, music21.clef.PercussionClef())
        score.insert(0, music21.meter.TimeSignature('5/4'))
        score.insert(0, music21.tempo.MetronomeMark('fast', 144, music21.note.Note(type='quarter')))
        return score
    
    def construct_score(self, part):
        df = self.generate_dataframe(part)
        form = self.csv_to_midi(df)
        comp = self.set_measure_zero(form)
        comp.write('midi', f'sifters/data/midi/{self.name}.mid')
        sorted = df.sort_values(by = 'Offset')
        sorted.to_csv(f'sifters/data/csv/{self.name}.csv', index=False)
        
class Percussion(Composition):
    def __init__(self, composition):
        self.name = 'Percussion'
        self.voices = composition.voices
        self.bin = composition.bin
        self.factors = composition.factors
        self.grid = composition.grid
        self.period = composition.period
        self.part = music21.stream.Score()
        
    def create_parts(self):
        parts = []
        for i in range(self.voices):
            p = music21.stream.Stream()
            for b in self.bin:
                p.insert(0, self.create_notes(b, self.factors[i]))
            for notes in p:
                parts.insert(0, notes)
        for p in parts:
            self.part.insert(0, p)
            
    def create_notes(self, bin, factor):
        part = music21.stream.Part()
        pattern = bin * factor
        dur = self.grid * (self.period / factor)
        events = self.midi_pool(bin)
        midi_pool = itertools.cycle(events)
        for i, bit in enumerate(pattern):
            if bit == 1:
                part.insert(i * dur, music21.note.Note(midi=next(midi_pool), quarterLength=self.grid))
        return part
    
    def midi_pool(self, bin):
        events = bin.count(1)
        lpf_slice = slice(0, self.get_largest_prime_factor(events))
        instrument_pool = itertools.cycle([60,61,62,63,64][lpf_slice])
        return [next(instrument_pool) for _ in range(events)]

    def construct_score(self):
        Composition.construct_score(self, self.part)

if __name__ == '__main__':
    sivs = '((8@0|8@1|8@7)&(5@1|5@3))', '((8@0|8@1|8@2)&5@0)', '((8@5|8@6)&(5@2|5@3|5@4))', '(8@6&5@1)', '(8@3)', '(8@4)', '(8@1&5@2)'
    comp = Composition(sivs)
    perc = Percussion(comp)
    perc.create_parts()
    perc.construct_score()