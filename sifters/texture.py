import decimal
import itertools

import numpy
import pandas


class Texture:
    
    texture_id = 1
        
    def __init__(self, mediator):
        
        self.texture_id = Texture.texture_id

        self.mediator = mediator
        
        self.binary = mediator.binary

        self.period = mediator.period

        # Find all occurences of 1 and derive an intervalic structure based on their indices.
        # self.intervals = [i for i in range(len(self.binary)) if self.binary[i] == 1]
        
        self.indices = numpy.nonzero(self.binary)[0]
    
        
        # # Derive modular-12 values from self.intervals. 
        # mod12 = list(range(12))
        # self.intervals = [mod12[i % len(mod12)] for i in self.intervals]
        
        # Set the factors attribute of the Texture object
        self.factors = [i for i in range(1, self.period + 1) if self.period % i == 0]
        
        self.notes_data = self.generate_notes_data()
        
        Texture.texture_id += 1


    def get_successive_diff(self, lst):
        return [0] + [lst[i+1] - lst[i] for i in range(len(lst)-1)]
    
    ### UPDATE THIS METHOD SO THAT MOD 12 IS NOT HARDCODEDf
    ### THINK OF RELATIONSHIP TO MICROTUNER IN ABLETON
    def segment_octave_by_period(self, period):
        interval = decimal.Decimal('12') / decimal.Decimal(str(period))
        return [interval * decimal.Decimal(str(i)) for i in range(period)]
    
    
    def generate_pitchclass_matrix(self, intervals):
        next_interval = intervals[1:]
        row = [next_interval[i] - intervals[0] for i in range(len(intervals) - 1)]

        matrix = [
            [
                (intervals[0] - row[i]) % (self.period - 1)
            ] 
            for i in range(len(intervals) - 1)
        ]

        row.insert(0, 0)
        matrix.insert(0, [intervals[0]])

        matrix = [
            [
                (matrix[i][0] + row[j]) % (self.period - 1)
                for j in range(len(matrix))
            ]
            for i in range(len(matrix))
        ]
        
        matrix = pandas.DataFrame(matrix,
                                index=[f'P{m[0]}' for m in matrix], 
                                columns=[f'I{i}' for i in matrix[0]])

        return matrix


    def generate_note_pool_from_matrix(self, matrix, num_of_positions, steps_cycle):
        pool = []
        current_index = 0
        retrograde = False

        for _ in range(num_of_positions):
            step = next(steps_cycle)
            wrapped_index = (current_index + abs(step)) % len(self.indices)
            wrap_count = (abs(step) + current_index) // len(self.indices)

            if wrap_count % 2 == 1:
                retrograde = not retrograde

            if step >= 0:
                if retrograde:
                    pool.append(matrix.iloc[wrapped_index][::-1].tolist())
                else:
                    pool.append(matrix.iloc[wrapped_index].tolist())
            if step < 0:
                if retrograde:
                    pool.append(matrix.iloc[:, wrapped_index][::-1].tolist())
                else:
                    pool.append(matrix.iloc[:, wrapped_index].tolist())

            current_index = wrapped_index

        return pool
    
    
    def generate_notes_data(self):
        notes_data = []

        for factor_index in range(len(self.factors)):
            tonality = decimal.Decimal(40.0)
            steps = self.get_successive_diff(self.indices)
            steps_cycle = itertools.cycle(steps)
            first_pitch = tonality + self.indices[0]

            segment = self.segment_octave_by_period(self.period)
            intervals = [segment[i] for i in self.indices]
            matrix = self.generate_pitchclass_matrix(self.indices)
            
            print(matrix)
            
            # matrix = first_pitch + self.generate_pitchclass_matrix(intervals)
        #     num_of_events = (len(self.intervals) * self.factors[factor_index])
        #     num_of_positions = num_of_events // len(steps)
        #     pool = self.generate_note_pool_from_matrix(matrix, num_of_positions, steps_cycle)
        #     flattened_pool = [num for list in pool for num in list]

        #     note_pool = itertools.cycle(flattened_pool)
        #     pattern = numpy.tile(self.binary, self.factors[factor_index])
        #     indices = numpy.nonzero(pattern)[0]
        #     duration = self.period // self.factors[factor_index]
            
        #     for index in indices:
        #         velocity = 64
        #         start = index * duration
        #         notes_data.append((self.texture_id, start, velocity, next(note_pool), duration))

        # return notes_data