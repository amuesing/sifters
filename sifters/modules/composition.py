from textures import *

import music21
import decimal
import fractions
import functools
import itertools
import decimal
import pandas
import numpy
import math

class Composition:
    
    
    def __init__(self, sieves, form=None):
        self.sieves = sieves
        self.period = None
        self.form = form if form is not None else 'Prime'
        self.binary = self.set_binary(sieves)


        self.factors = [i for i in range(1, self.period + 1) if self.period % i == 0]
        self.changes = [[tupl[1] for tupl in sublist] for sublist in self.get_consecutive_count()]
        self.form = self.distribute_changes(self.changes)
        self.grids_set = self.set_grids()

        # Find all occurences of 1 and derive an intervalic structure based on their indices.
        self.intervals = [[j for j in range(len(self.binary[i])) if self.binary[i][j] == 1] for i in range(len(self.binary))]
        
        # Derive modular-12 values from self.intervals. 
        mod12 = list(range(12))
        self.closed_intervals = [[mod12[j % len(mod12)] for j in i] for i in self.intervals]
        self.repeats = self.set_repeats()
        # self.multipliers = self.get_least_common_multiple(self.normalized_numerators)
        # self.ticks_per_beat = 480
        # self.notes_data = self.set_notes_data()


        # self.normalized_numerator = numpy.array([self.normalize_numerator(arg, self.get_multiplier(arg)) for arg in self.kwargs.values()])
        # self.set_textures()
        # self.textures = self.set_textures()
        

    def set_binary(self, sieves):

        def get_binary(sieves):
             
            binary = []
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
                row = [decimal.Decimal('0.0')] + [next_interval[i] - intervals[0] for i, _ in enumerate(intervals[:-1])]

                # Normalize the tone row so that it starts with 0 and has no negative values.
                row = [n % 12 for n in row]

                # Generate the rows of the pitch class matrix.
                matrix = [[(abs(note - 12) % 12)] for note in row]

                # Generate the columns of the pitch class matrix.
                matrix = [r * len(intervals) for r in matrix]

                # Update the matrix with the correct pitch class values.
                matrix = [[(matrix[i][j] + row[j]) % 12
                        for j, _ in enumerate(range(len(row)))]
                        for i in range(len(row))]

                # Label the rows and columns of the matrix.
                matrix = pandas.DataFrame(matrix,
                                        index=[f'P{m[0]}' for m in matrix], 
                                        columns=[f'I{i}' for i in matrix[0]])

                return matrix
            
            
            # Set the base tonality value.
            tonality = decimal.Decimal(40.0)
            
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
                
                # Find the multiplier for self.grid to normalize duration length against number of repetitions of sieve in pattern.
                duration_multiplier = self.period // self.factors[j]
                
                # Convert the grid Fraction object into a Decimal object.
                grid = decimal.Decimal(self.grid.numerator) / decimal.Decimal(self.grid.denominator)
                
                # Find the duration of each note represented as a decimal.
                duration = grid * duration_multiplier

                # For each non-zero indice append notes_data list with corresponding note information.
                for k in indices:
                    velocity = 64
                    offset = decimal.Decimal(int(k)) * duration
                    notes_data.append([round(offset, 6), velocity, next(note_pool), round(grid, 6)])

        notes_data = [[data[0], data[1], data[2], data[3]] for data in notes_data]
        
        return pandas.DataFrame(notes_data, columns=['Start', 'Velocity', 'Note', 'Duration']).sort_values(by='Start').drop_duplicates().reset_index(drop=True)
    

    def get_consecutive_count(self):
        lst = self.binary
        result = []  # List to store the consecutive counts for each original list.

        for sieve in lst:
            consecutive_counts = []  # List to store the consecutive counts for the current original list.
            consecutive_count = 1  # Initialize the count with 1 since the first element is always consecutive.
            current_num = sieve[0]  # Initialize the current number with the first element.

            # Iterate over the elements starting from the second one.
            for num in sieve[1:]:
                if num == current_num:  # If the current number is the same as the previous one.
                    consecutive_count += 1
                else:  # If the current number is different than the previous one.
                    consecutive_counts.append((current_num, consecutive_count))  # Store the number and its consecutive count.
                    consecutive_count = 1  # Reset the count for the new number.
                    current_num = num  # Update the current number.

            # Add the count for the last number.
            consecutive_counts.append((current_num, consecutive_count))

            # Add the consecutive counts for the current original list to the result.
            result.append(consecutive_counts)

        return result
    
    
    def distribute_changes(self, changes):
        
        structured_lists = []
        
        for lst in changes:
            
            sieve_layer = []
            
            for num in lst:
                sublist = lst.copy() # Create a copy of the original list
                
                repeated_list = []
                
                for _ in range(num):
                    repeated_list.append(sublist) # Append the elements of sublist to repeated_list
                    
                sieve_layer.append(repeated_list)
                
            structured_lists.append(sieve_layer)
        
        return structured_lists
    
    
    def flatten_list(self, nested_list):
        
        flattened_list = []
        
        for item in nested_list:
            
            if isinstance(item, list):
                flattened_list.extend(self.flatten_list(item))
                
            else:
                flattened_list.append(item)
                
        return flattened_list
    


    def get_percent_of_period(self, lst):

        percent_of_period = [[(decimal.Decimal(num) / decimal.Decimal(self.period)).quantize(decimal.Decimal('0.000')) for num in l] for l in lst]

        return percent_of_period


    @staticmethod
    def convert_decimal_to_fraction(decimal_list):
        
        fraction_list = []

        for sublist in decimal_list:
            fraction_sublist = []
            
            for decimal in sublist:
                fraction = fractions.Fraction(decimal)
                fraction_sublist.append(fraction)
                
            fraction_list.append(fraction_sublist)

        return fraction_list
    
    
    @staticmethod
    def get_unique_fractions(input_list):
        
        unique_fractions = []
        
        for sublist in input_list:
            
            unique_sublist = []
            unique_set = set()
            
            for fraction in sublist:
                fraction_str = str(fraction)
                
                if fraction_str not in unique_set:
                    unique_set.add(fraction_str)
                    unique_sublist.append(fraction)
            
            unique_fractions.append(unique_sublist)
        
        return unique_fractions
    
    
    @staticmethod
    def lcm_of_decimals(decimals):
        
        max_decimal_places = max([str(decimal)[::-1].find('.') for decimal in decimals])
        integers = [round(decimal * 10 ** max_decimal_places) for decimal in decimals]
        lcm_of_integers = math.lcm(*integers)
        lcm_of_decimals = lcm_of_integers / (10 ** max_decimal_places)
        return lcm_of_decimals

    
    def set_grids(self):
        
        percent = self.get_percent_of_period(self.changes)
        
        grids = self.convert_decimal_to_fraction(percent)
        
        grids = self.get_unique_fractions(grids)
        
        # # Flatten the nested lists into a single list
        # flat_list = self.flatten_list(percent)
        
        # # Remove duplicates and get the unique values
        # unique_values = list(set(flat_list))
        
        # lcm = [self.lcm_of_decimals(lst) for lst in percent]
        
        return grids
    
    def set_textures(self):
        for sieve, grids in zip(self.sieves, self.grids):
            for grid in grids:
                print(sieve, grid)

        
        # return monophonic.Monophonic(self.sieves, self.grids)

    def set_repeats(self):

        def set_normalized_numerators(grids):

            def find_lcd(denominators):
                if isinstance(denominators, list):
                    sub_lcd = [find_lcd(lst) for lst in denominators]
                    return functools.reduce(math.lcm, sub_lcd)
                else:
                    return denominators
            
            numerators = [[fraction.numerator for fraction in sublist] for sublist in grids]

            denominators = [[fraction.denominator for fraction in sublist] for sublist in grids]
            
            lcd = find_lcd(denominators)

            multipliers = [[lcd // fraction.denominator for fraction in sublist] for sublist in grids]

            normalized_numerators = [[num * mult for num, mult in zip(num_list, mult_list)] for num_list, mult_list in zip(numerators, multipliers)]

            return normalized_numerators
        
        normalized_numerators = set_normalized_numerators(self.grids_set)

        multipliers = []

        for lst in normalized_numerators:
            lcm = self.get_least_common_multiple(lst)
            multipliers.append([lcm // num for num in lst])

        print(multipliers)



    @staticmethod
    def group_by_start(dataframe):
        # Get all column names in the DataFrame
        columns = dataframe.columns

        # Check if 'Start' is one of the column names
        if 'Start' in columns:
            # Sort the DataFrame based on the 'Start' column
            dataframe = dataframe.sort_values('Start')
            
            # Group the sorted DataFrame by the 'Start' column and create a new DataFrame with lists of values
            agg_dict = {col: list for col in columns if col != 'Start'}  # Exclude 'Start' column from aggregation
            dataframe = dataframe.groupby('Start').agg(agg_dict).reset_index()

        return dataframe


    @staticmethod
    def get_closest_note(dataframe):
        
        # Iterate over the dataframe rows
        for i in range(len(dataframe)):
            current_row = dataframe.loc[i]

            if len(current_row['Note']) > 1:
                min_note_index = current_row['Note'].index(min(current_row['Note']))
                selected_note_value = current_row['Note'][min_note_index]
                dataframe.loc[i, 'Note'] = [selected_note_value]
                dataframe.loc[i, 'Velocity'] = [current_row['Velocity'][min_note_index]]
                dataframe.loc[i, 'Duration'] = [current_row['Duration'][min_note_index]]

            if i < len(dataframe) - 1:
                next_row = dataframe.loc[i + 1]

                if len(current_row['Note']) == 1 and len(next_row['Note']) > 1:
                    current_note = current_row['Note'][0]
                    next_note_values = next_row['Note']
                    closest_note = min(next_note_values, key=lambda x: abs(x - current_note))
                    dataframe.loc[i + 1, 'Note'] = [closest_note]
                    dataframe.loc[i + 1, 'Velocity'] = next_row['Velocity'][next_note_values.index(closest_note)]
                    dataframe.loc[i + 1, 'Duration'] = next_row['Duration'][next_note_values.index(closest_note)]

        # Print the updated dataframe
        return dataframe
        
    # If I run check_and_close_intervals I will get values that are too low or too high. (negative numbers)
    def check_and_close_intervals(self, dataframe):
        
        for i in range(len(dataframe['Note']) - 1):
            if abs(dataframe['Note'][i] - dataframe['Note'][i + 1]) > 6: 
                dataframe = self.close_intervals(dataframe)
                return self.check_and_close_intervals(dataframe)
            
        return dataframe
    
    
    @staticmethod
    def close_intervals(dataframe):
        
        # Make a copy of the input dataframe.
        updated_dataframe = dataframe.copy()
        
        # Iterate through each pair of consecutive note values.
        for i, note in enumerate(updated_dataframe['Note'][:-1]):
            next_note = updated_dataframe['Note'][i + 1]
            
            # If the increase between note notes is greater than a tritone, transpose
            # the next note note up one octave.
            if note - next_note > 6:
                updated_dataframe.at[i + 1, 'Note'] = next_note + 12
            
            # If the decrease between note notes is greater than a tritone, transpose
            # the next note note down one octave.
            elif note - next_note < -6:
                updated_dataframe.at[i + 1, 'Note'] = next_note - 12
        
        # Return the updated dataframe.
        return updated_dataframe
    
        
    @staticmethod
    def adjust_note_range(dataframe):
        
        # Define the lambda function to adjust values outside the range [36, 60].
        adjust_value = lambda x: x - 12 if x > 60 else (x + 12 if x < 36 else x)
        
        # Apply the lambda function repeatedly until all values satisfy the condition.
        while dataframe['Note'].apply(lambda x: x < 36 or x > 60).any():
            dataframe['Note'] = dataframe['Note'].apply(adjust_value)
            
        return dataframe
    
    
    @staticmethod
    def combine_consecutive_note_values(dataframe):
    
        i = 0
        while i < len(dataframe) - 1:
            if dataframe.loc[i, 'Note'] == dataframe.loc[i + 1, 'Note']:
                if (dataframe.loc[i, 'Start'] + dataframe.loc[i, 'Duration']) < dataframe.loc[i + 1, 'Start']:
                    i += 1
                else:
                    dataframe.loc[i, 'Duration'] += dataframe.loc[i + 1, 'Duration']
                    dataframe = dataframe.drop(i + 1).reset_index(drop=True)
            else:
                i += 1

        return dataframe
    
    
    @staticmethod
    def convert_lists_to_scalars(dataframe):
        
        # Iterate over each column in the dataframe
        for col in dataframe.columns:
            # Check if the column contains objects (lists or tuples)
            if dataframe[col].dtype == object:
                # Apply a lambda function to each value in the column
                # If the value is a list or tuple of length 1, replace it with the single value
                dataframe[col] = dataframe[col].apply(lambda x: x[0] if isinstance(x, (list, tuple)) else x)
        
        return dataframe
    
    
    def get_least_common_multiple(self, nums):
        if len(nums) == 2:
            return nums[0] * nums[1] // math.gcd(nums[0], nums[1])
        elif len(nums) > 2:
            middle = len(nums) // 2
            left_lcm = self.get_least_common_multiple(nums[:middle])
            right_lcm = self.get_least_common_multiple(nums[middle:])
            return left_lcm * right_lcm // math.gcd(left_lcm, right_lcm)
        else:
            return nums[0]
        
        
if __name__ == '__main__':
    
    sieves = [
    
    '((8@0|8@1|8@7)&(5@1|5@3))', 
    '((8@0|8@1|8@2)&5@0)',
    '((8@5|8@6)&(5@2|5@3|5@4))',
    '(8@6&5@1)',
    '(8@3)',
    '(8@4)',
    '(8@1&5@2)'
    
    ]
    
    # sieves = ['|'.join(sieves)]
        
    comp = Composition(sieves)