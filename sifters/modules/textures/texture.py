from modules.composition import *

import music21
import fractions
import itertools
import decimal
import pandas
import numpy

class Texture(Composition):
    
    grid_history = []
    texture_id = 1
        
    def __init__(self, sieves, grid=None, form=None):
        
        # Set the grid attribute of the Texture object
        self.grid = fractions.Fraction(grid) if grid is not None else fractions.Fraction(1, 1)
        
        # Set the form attribute of the Texture object
        self.form = form if form is not None else 'Prime'
        
        # Set the binary attribute of the Texture object
        self.binary = self.set_binary(sieves)
        
        # Find all occurences of 1 and derive an intervalic structure based on their indices.
        self.intervals = [[j for j in range(len(self.binary[i])) if self.binary[i][j] == 1] for i in range(len(self.binary))]
        
        # Derive modular-12 values from self.intervals. 
        mod12 = list(range(12))
        self.closed_intervals = [[mod12[j % len(mod12)] for j in i] for i in self.intervals]
        
        # Set the factors attribute of the Texture object
        self.factors = [i for i in range(1, self.period + 1) if self.period % i == 0]
        
        # Add the current grid value to the grid history list
        self.grid_history.append(self.grid)
        
        # Set the texture ID attribute of the Texture object
        self.texture_id = Texture.texture_id
        
        # Increment the texture ID for the next Texture object
        Texture.texture_id += 1
        
        
    def set_binary(self, sieves):

        def get_binary(sieves):
                    
            binary = []
            
            # If the input is a tuple, compute the binary representation for each sieve.
            if isinstance(sieves, list):
                periods = []
                objects = []
                for siev in sieves:
                    obj = music21.sieve.Sieve(siev)
                    objects.append(obj)
                    periods.append(obj.period())
                    
                # Compute the least common multiple of the periods of the input sieves.
                self.period = self.get_least_common_multiple(periods)
                
                # Set the Z range of each Sieve object and append its binary representation to the list.
                for obj in objects:
                    obj.setZRange(0, self.period - 1)
                    binary.append(obj.segment(segmentFormat='binary'))
            else:
                # Compute the binary representation for the single input sieve.
                for siv in sieves:
                    object = music21.sieve.Sieve(siv)
                    object.setZRange(0, object.period() - 1)
                    binary.append(object.segment(segmentFormat='binary'))
                
            return binary
        
        # Convert the list of sets of intervals to their binary forms
        binary = get_binary(sieves)
        
        # Define a dictionary with lambda functions to transform the binary forms into different forms
        forms = {
            'Prime': lambda bin: bin,
            'Inversion': lambda bin: [1 if x == 0 else 0 for x in bin],
            'Retrograde': lambda bin: bin[::-1],
            'Retrograde-Inversion': lambda bin: [1 if x == 0 else 1 for x in bin][::-1]
        }
        
        # Apply the selected form to each binary form in the list, and return the resulting list
        return [forms[self.form](bin) for bin in binary]
    
    
    def set_notes_data(self):
        
        def generate_note_pool(binary_index, factor_index):
            
            def get_successive_diff(lst):
                return [0] + [lst[i+1] - lst[i] for i in range(len(lst)-1)]
            
            
            def segment_octave_by_period(period):
                interval = decimal.Decimal('12') / decimal.Decimal(str(period))
                return [interval * decimal.Decimal(str(i)) for i in range(period)]
            
            
            def generate_pitchclass_matrix(intervals):
                        
                # Calculate the interval between each pair of consecutive pitches.
                next_interval = intervals[1:]
                row = [0] + [next_interval[i] - intervals[0] for i, _ in enumerate(intervals[:-1])]
                
                # Normalize the tone row so that it starts with 0 and has no negative values.
                row = [decimal.Decimal(n) % decimal.Decimal('12') for n in row]
                
                # Generate the rows of the pitch class matrix.
                matrix = [[abs(note - decimal.Decimal('12')) % decimal.Decimal('12')] for note in row]
                
                # Generate the columns of the pitch class matrix.
                matrix = [r * len(intervals) for r in matrix]
                
                # Update the matrix with the correct pitch class values.
                matrix = [[(matrix[i][j] + row[j]) % decimal.Decimal('12')
                        for j, _ in enumerate(range(len(row)))]
                        for i in range(len(row))]
                
                # Label the rows and columns of the matrix.
                matrix = pandas.DataFrame(matrix,
                                        index=[f'P{m[0]}' for m in matrix], 
                                        columns=[f'I{i}' for i in matrix[0]]).astype(float)
                
                return matrix
            
            
            # Set the base tonality value.
            tonality = 40
            
            # Generate a list of successieve differences between the intervals.
            steps = get_successive_diff(self.closed_intervals[binary_index])
            
            # Create a cycle iterator for the steps list.
            steps_cycle = itertools.cycle(steps)
            
            # Compute the starting pitch for the sieve.
            first_pitch = tonality + self.closed_intervals[binary_index][0]
            
            # Get the indices of non-zero elements in the sieve.
            indices = numpy.nonzero(self.binary[binary_index])[0]
            
            # Get the intervals associated with the non-zero elements.
            segment = segment_octave_by_period(self.period)
            intervals = [segment[i] for i in indices]
            
            # Generate a pitch matrix based on the intervals.
            matrix = first_pitch + generate_pitchclass_matrix(intervals)
            
            # Compute the number of events and positions needed for the sieve.
            num_of_events = (len(self.closed_intervals[binary_index]) * self.factors[factor_index])
            num_of_positions = num_of_events // len(steps)
            
            # Generate the note pool by iterating through the steps and matrix.
            pool = []
            current_index = 0
            retrograde = False
            for _ in range(num_of_positions):
                step = next(steps_cycle)
                wrapped_index = (current_index + abs(step)) % len(self.intervals[binary_index])
                
                # Check if the intervals have wrapped around the range of the matrix.
                wrap_count = (abs(step) + current_index) // len(self.intervals[binary_index])
                
                # If the interval wraps the length of the matrix an odd number of times update retrograde.
                if wrap_count % 2 == 1:
                    if retrograde == False:
                        retrograde = True
                    else:
                        retrograde = False
                
                # Append the appropriate row or column of the matrix to the pool.
                if step >= 0:
                    if retrograde == True:
                        pool.append(matrix.iloc[wrapped_index][::-1].tolist())
                    else:
                        pool.append(matrix.iloc[wrapped_index].tolist())
                if step < 0:
                    if retrograde == True:
                        pool.append(matrix.iloc[:, wrapped_index][::-1].tolist())
                    else:
                        pool.append(matrix.iloc[:, wrapped_index].tolist())
                
                current_index = wrapped_index
            
            # Flatten the pool into a 1D list of note values.
            flattened_pool = [num for list in pool for num in list]
            return flattened_pool
        
        
        # Create a list container for notes_data.
        notes_data = []
        
        # Create an iterator which is equal to the length of a list of forms represented in binary.
        for i in range(len(self.binary)):
            
            # Create an iterator which is equal to the length of a list of factors (for self.period).
            for j in range(len(self.factors)):
                
                # Create a note_pool for each sieve represented in self.binary.
                note_pool = itertools.cycle(generate_note_pool(i, j))
                
                # Repeat form a number of times sufficient to normalize pattern length against sieves represented in self.binary.
                pattern = numpy.tile(self.binary[i], self.factors[j])
                
                # Create a list of indices where non-zero elements occur within the pattern.
                indices = numpy.nonzero(pattern)[0]
                
                # Find the multiplier for self.grid to normalize duration length against number of repititions of sieve in pattern.
                duration_multiplier = self.period / self.factors[j]
                
                # Find the duration of each note represented as a float.
                duration = self.grid * duration_multiplier
                
                # For each non-zero indice append notes_data list with corresponding note information.
                for k in indices:
                    velocity = 64
                    offset = k * duration
                    notes_data.append([offset, velocity, next(note_pool), float(self.grid)])
                    
        notes_data = [[round(data[0], 6), data[1], data[2], round(data[3], 6)] for data in notes_data]
        
        self.notes_data = pandas.DataFrame(notes_data, columns=['Start', 'Velocity', 'Note', 'Duration']).sort_values(by='Start').drop_duplicates().reset_index(drop=True)