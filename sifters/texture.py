import decimal
import itertools

import math
import numpy
import pandas


class Texture:
    
    texture_id = 1
        
    def __init__(self, mediator):
        
        self.texture_id = Texture.texture_id

        self.mediator = mediator
        
        self.binary = mediator.binary

        self.period = mediator.period
        
        self.indices = numpy.nonzero(self.binary)[0]
        
        # Set the factors attribute of the Texture object
        self.factors = [i for i in range(1, self.period + 1) if self.period % i == 0]
        
        self.scale = self.segment_octave_by_period_in_cents()
        
        self.notes_data = self.generate_notes_data()
        
        Texture.texture_id += 1


    def get_successive_diff(self, lst):
        return [0] + [lst[i+1] - lst[i] for i in range(len(lst)-1)]

    
    def segment_octave_by_period_in_cents(self):
        cents = []

        # Calculate cents based on equal temperament
        for i in range(1, self.period + 1):
            cent_value = (1200 / self.period) * i
            cent_value = round(cent_value, 6)
            cents.append(cent_value)


        return cents
    
    
    def create_tuning_file(title, description, floats_list, file_name):
        # Construct the file_content
        file_content = f"""! {title}
                        !
                        {description}
                        {len(floats_list)}
                        !
                        """

        # Add floats to the content
        file_content += "\n".join(map(str, floats_list))

        # Open the file in write mode ('w')
        with open(file_name, 'w') as file:
            # Write content to the file
            file.write(file_content)


    def generate_pitchclass_matrix(self, intervals):
        next_interval = intervals[1:]
        row = [next_interval[i] - intervals[0] for i in range(len(intervals) - 1)]
        
        matrix = [
            [
                (0 - row[i]) % (self.period - 1)
            ] 
            for i in range(len(intervals) - 1)
        ]

        row.insert(0, 0)
        matrix.insert(0, [0])

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
            steps = self.get_successive_diff(self.indices)
            steps_cycle = itertools.cycle(steps)

            matrix = self.indices[0] + self.generate_pitchclass_matrix(self.indices)

            num_of_events = (len(self.indices) * self.factors[factor_index])
            num_of_positions = num_of_events // len(steps)
            pool = self.generate_note_pool_from_matrix(matrix, num_of_positions, steps_cycle)
            flattened_pool = [num for list in pool for num in list]

            note_pool = itertools.cycle(flattened_pool)
            pattern = numpy.tile(self.binary, self.factors[factor_index])
            indices = numpy.nonzero(pattern)[0]
            duration = self.period // self.factors[factor_index]
            
            for index in indices:
                velocity = 64
                start = index * duration
                notes_data.append((self.texture_id, start, velocity, next(note_pool), duration))
                
        return notes_data