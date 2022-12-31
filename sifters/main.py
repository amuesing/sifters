from music21 import *
from itertools import *
from modules import *

def main():
    c = Composition(utilities.load_pickle('.data/sivs.p'))
    c.construct()
class Composition:
    def __init__(self, sivs):
        self.score = stream.Score()
        self.intervals = initialize.intervals(sivs)
        self.binary = initialize.binary(sivs)
        self.period = len(self.binary[0])
        self.factors = utilities.factorize(self.period)
        self.grid = 1

    def generate_score(self):
        factors = self.factors
        voices = len(factors)
        parts = []
        part_number = 1
        for _ in range(voices):
            part = stream.Stream()
            p = stream.Stream()
            for bin in self.binary:
                p.insert(0, self.generate_percussion(bin, factors[part_number - 1]))
            for i in p:
                parts.insert(0, i)
            part_number += 1
        for part in parts:
            self.score.insert(0, part)
    
    def generate_percussion(self, bin, factor):
        part = stream.Part()
        repeat = 1
        pattern = (bin * factor) * repeat
        dur = self.grid * (self.period/factor)
        events = formalize.midi_pool(bin)
        midi_pool = cycle(events)
        i = 0
        for bit in pattern:
            if bit == 1:
                part.insert(i * dur, note.Note(midi=next(midi_pool), quarterLength=self.grid))
            i += 1
        return part
    
    def construct(self):
        self.generate_score()
        df = formalize.generate_dataframe(self.score)
        form = formalize.csv_to_midi(df, self.grid)
        comp = formalize.measure_zero(form)
        comp.write('midi', '.data/percussion.mid')

if __name__ == '__main__':
    main()