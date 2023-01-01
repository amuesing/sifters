import music21 as music21
import numpy as np
import pandas as pd
import percussion as perc

class Score:
    def __init__(self, sivs):
        self.percussion_part = music21.stream.Score()
        self.intervals = Score.intervals(sivs)
        self.binary = Score.binary(sivs)
        self.period = len(self.binary[0])
        self.factors = Score.factorize(self.period)
        self.voices = len(self.factors)
        self.grid = 1
        
    def construct(self):
        # how to avoid circular import?
        perc.Percussion.part(self)
        self.percussion_part.show('text')
        df = Score.generate_dataframe(self.percussion_part)
        form = Score.csv_to_midi(df, self.grid)
        comp = Score.measure_zero(form)
        comp.write('midi', '.data/percussion.mid')
    
    def binary(siev):
        bin = []
        if type(siev) == tuple:
            i = 0
            per = []
            obj = []
            for siv in siev:
                objects = music21.sieve.Sieve(siv)
                obj.append(objects)
                per.append(objects.period())
            lcm = np.lcm.reduce(per)
            for o in obj:
                o.setZRange(0, lcm - 1)
                bin.append(o.segment(segmentFormat='binary'))
                i += 1
        else:
            obj = music21.sieve.Sieve(siev)
            obj.setZRange(0, obj.period() - 1)
            bin.append(obj.segment(segmentFormat='binary'))
        return bin

    def intervals(siev):
        intervals = []
        for siv in siev:
            set = music21.sieve.Sieve(siv)
            set.setZRange(0, set.period() - 1)
            intervals.append(set.segment())
        return intervals
    
    # https://stackoverflow.com/questions/47064885/list-all-factors-of-number
    def factorize(num):
        return [n for n in range(1, num + 1) if num % n == 0]
    
    # https://www.w3resource.com/python-exerc
    def largest_prime_factor(n):
        if n == 1:
            return 1
        else:
            return next(n // i for i in range(1, n) if n % i == 0 and Score.is_prime(n // i))

    def is_prime(m):
        return all(m % i for i in range(2, m - 1))
    
    # https://medium.com/swlh/music21-pandas-and-condensing-sequential-data-1251515857a6  
    def generate_dataframe(score):
        parts = score.parts
        rows_list = []
        for part in parts:
            for _, elt in enumerate(part.flat
                    .stripTies()
                    .getElementsByClass(
                [music21.note.Note, music21.note.Rest, music21.chord.Chord, music21.bar.Barline])):
                if hasattr(elt, 'pitches'):
                    pitches = elt.pitches
                    for pitch in pitches:
                        rows_list.append(Score.generate_row(elt, pitch.midi))
                else:
                    rows_list.append(Score.generate_row(elt))
        return Score.remove_duplicates(pd.DataFrame(rows_list))
    
    def remove_duplicates(df):
        return df.drop_duplicates()
    
    def generate_row(mus_object, midi):
        d = {}
        d.update({'Offset': mus_object.offset,
                'Midi': midi})
        return d
        
    def csv_to_midi(df, grid):
        part = music21.stream.Score()
        elem = []
        result = {}
        fiveInFour = music21.duration.Tuplet(5,4)
        fiveInFour.setDurationType('16th')
        for _, row in df.iterrows():
            offset = row['Offset']
            mid = row['Midi']
            elem.append([offset, int(mid)])
        for sublist in elem:
            if sublist[0] in result:
                result[sublist[0]].append(sublist[1])
            else:
                result[sublist[0]] = [sublist[1]]
        for offset, mid in result.items():
            if len(mid) > 1:
                part.insert(offset, music21.chord.Chord(mid, quarterLength=grid))
            else:
                part.insert(offset, music21.note.Note(mid[0], quarterLength=grid))
        return part.makeRests(fillGaps=True)
    
    def measure_zero(s):
        s.insert(0, music21.metadata.Metadata())
        s.metadata.title = 'Sifters'
        s.metadata.composer = 'Ari Müsing'
        s.insert(0, music21.instrument.UnpitchedPercussion())
        s.insert(0, music21.clef.PercussionClef())
        s.insert(0, music21.meter.TimeSignature('5/4'))
        s.insert(0, music21.tempo.MetronomeMark('fast', 144, music21.note.Note(type='quarter')))
        return s  

if __name__ == '__main__':
    sivs = '((8@0|8@1|8@7)&(5@1|5@3))', '((8@0|8@1|8@2)&5@0)', '((8@5|8@6)&(5@2|5@3|5@4))', '(8@6&5@1)', '(8@3)', '(8@4)', '(8@1&5@2)'
    comp = Score(sivs)
    comp.construct()