import itertools

import numpy
import pandas

class Texture:
    texture_id = 1
        
    def __init__(self, mediator):
        
        self.texture_id = Texture.texture_id

        self.mediator = mediator
        
        self.binary = mediator.binary
        
        self.indices = numpy.nonzero(self.binary)[0]

        self.period = mediator.period
        
        # Set the factors attribute of the Texture object
        self.factors = [i for i in range(1, self.period + 1) if self.period % i == 0]

        self.notes_data = self.generate_notes_data()
        
        Texture.texture_id += 1
    
    
    def get_successive_diff(self, integers):
        return [0] + [integers[i+1] - integers[i] for i in range(len(integers)-1)]
    
    
    def represent_by_size(self, steps):
        sorted_list = sorted(steps)
        sorted_set = set(sorted_list)

        # Create a dictionary to store the index for each value
        index_mapping = {value: rank for rank, value in enumerate(sorted_set)}

        # Map each element in the original list to its index in the sorted set
        steps = [index_mapping[value] for value in steps]
        
        return steps

    
    def unflatten_list(self, flat_list, original_matrix):
        # Assuming original_matrix is a list of lists
        rows, cols = len(original_matrix), len(original_matrix[0])

        # Reshape the flat_list back to the original matrix shape
        reshaped_matrix = [flat_list[i * cols:(i + 1) * cols] for i in range(rows)]

        return reshaped_matrix
    
    
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

        return matrix
    
    
    def represent_matrix_by_size(self, matrix):
        flattened_matrix = [value for lst in matrix for value in lst]
        
        sized_matrix = self.represent_by_size(flattened_matrix)

        # Unflatten the sized list back to the original matrix structure
        matrix = self.unflatten_list(sized_matrix, matrix)
        
        return matrix
    
    
    def convert_matrix_to_dataframe(self, matrix):
        # Convert the unflattened matrix to a DataFrame
        matrix = pandas.DataFrame(matrix,
                                    index=[f'P{m[0]}' for m in matrix], 
                                    columns=[f'I{i}' for i in matrix[0]])
        
        return matrix
    
    
    def generate_note_pool_from_matrix(self, matrix, num_of_positions, steps):
        pool = []
        current_index = 0
        retrograde = False
        steps_cycle = itertools.cycle(steps)

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
    
    
    def create_tuning_file(self, floats_list):
        title = f'Base {self.period} Tuning'
        description = 'Tuning based on the periodicity of a logical sieve, selecting for degrees that coorespond to non-zero sieve elements.'
        file_name = 'data/scl/tuning.scl'
        # Construct the file_content
        file_content = f'''! {title}
!
{description}
{len(floats_list) + 1}
!
'''

        # Add floats to the content
        file_content += '\n'.join(map(str, floats_list))
        
        # Add '2/1' on its own line
        file_content += '\n2/1'

        # Open the file in write mode ('w')
        with open(file_name, 'w') as file:
            # Write content to the file
            file.write(file_content)
        
    
    def select_scalar_segments(self, indice_list):
        cents = []

        for i in range(self.period):
            cent_value = (1200 / self.period) * i
            cent_value = round(cent_value, 6)
            cents.append(cent_value)

        # Select cents at specific indices
        self.selected_cents_implied_zero = [cents[index - indice_list[0]] for index in indice_list][1:]

        # Create tuning file using the selected cents
        self.create_tuning_file(self.selected_cents_implied_zero)

        # Return the original list of cents
        return cents

    
    def generate_notes_data(self):
        notes_data = []
        indice_list = []
        
        steps = self.get_successive_diff(self.indices)
        normalized_matrix = self.generate_pitchclass_matrix(self.indices)
        matrix_represented_by_size = self.represent_matrix_by_size(normalized_matrix)
        matrix_represented_by_size = self.convert_matrix_to_dataframe(matrix_represented_by_size)
        matrix_adjusted_by_step = self.indices[0] + normalized_matrix
        matrix_adjusted_by_step = self.convert_matrix_to_dataframe(matrix_adjusted_by_step)
        
        # For each factor, create exactly the number of notes required for each texture to achieve parity
        for factor_index in range(len(self.factors)):
            num_of_events = (len(self.indices) * self.factors[factor_index])
            num_of_positions = num_of_events // len(steps)
            pool = self.generate_note_pool_from_matrix(matrix_represented_by_size, num_of_positions, steps)
            adjusted_pool = self.generate_note_pool_from_matrix(matrix_adjusted_by_step, num_of_positions, steps)
            flattened_pool = [num for list in pool for num in list]
            indice_list = [num for list in adjusted_pool for num in list]

            note_pool = itertools.cycle(flattened_pool)
            tiled_pattern = numpy.tile(self.binary, self.factors[factor_index])
            tiled_indices = numpy.nonzero(tiled_pattern)[0]

            duration = self.period // self.factors[factor_index]
            
            for index in tiled_indices:
                velocity = 64
                start = index * duration
                notes_data.append((self.texture_id, start, velocity, next(note_pool), duration))
        
        self.select_scalar_segments(list(set(indice_list)))
        return notes_data