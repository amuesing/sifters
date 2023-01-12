class Bass(Composition):
    def __init__(self, sivs):
        super().__init__(sivs)
        self.stream = music21.stream.Score()
        self.name = 'Bass'
        self.ratio = 1
        self.grid = self.grid * self.ratio
        self.period = len(self.bin[0]) / self.ratio
        self.factors = Composition.get_factors(self.period)
        self.create_parts()
        
        # for i, _ in enumerate(range(len(self.factors))):
        #     for b in self.bin:
        #         self.stream.insert(0, self.create_notes(i, b))
        #     print(i)
        
    def create_parts(self):
        for i, _ in enumerate(range(len(self.factors))):
            for b in self.bin:
                self.stream.insert(0, self.create_notes(i, b))
        # index = 0
        # for _ in range(len(self.factors)):
        #     for i, b in enumerate(self.bin):
        #         self.stream.insert(0, self.create_notes(i, b))
        #         print(i)
        #     index += 1
            # print(self.intervals)
        
    def create_notes(self, index, bin):
        part = music21.stream.Part()
        # pattern = bin * int(self.period)
        pattern = bin * self.factors[index]
        dur = self.grid * (self.period / self.factors[index])
        # midi_pool = itertools.cycle(self.midi_pool(index))
        midi_pool = itertools.cycle([40, 44, 47, 41, 45, 48, 50, 52])
        for i, bit in enumerate(pattern):
            if bit == 1:
                part.insert(i * dur, music21.note.Note(midi=next(midi_pool), quarterLength=self.grid))
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