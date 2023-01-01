from music21 import *
from itertools import cycle
from score import Score

class Percussion(Score):
    def __init__(self, percussion_part, intervals, binary, period, voices, grid):
        super().__init__(percussion_part, intervals, binary, period, voices, grid)
    
    def part(self):
        parts = []
        part_number = 1
        for _ in range(self.voices):
            p = stream.Stream()
            for bin in self.binary:
                p.insert(0, Percussion.note(self, bin, self.factors[part_number - 1]))
            for i in p:
                parts.insert(0, i)
            part_number += 1
        for part in parts:
            self.percussion_part.insert(0, part)
            
    def note(self, bin, factor):
        part = stream.Part()
        repeat = 1
        pattern = (bin * factor) * repeat
        dur = self.grid * (self.period/factor)
        events = Percussion.midi_pool(bin)
        midi_pool = cycle(events)
        i = 0
        for bit in pattern:
            if bit == 1:
                part.insert(i * dur, note.Note(midi=next(midi_pool), quarterLength=self.grid))
            i += 1
        return part
    
    def midi_pool(bin):
        midi_pool = []
        events = (bin.count(1))
        lpf_slice = slice(0, Score.largest_prime_factor(events))
        # how to determine number of instrument elements present/distribution of elements
        # instruments = cycle([35, 44, 60, 76, 80][lpf_slice])
        instrument_pool = cycle([60,61,62,63,64][lpf_slice])
        for _ in range(events):
            midi_pool.append(next(instrument_pool))
        return midi_pool
    
if __name__ == '__main__':
    Percussion()