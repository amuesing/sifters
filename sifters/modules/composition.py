from textures import *

import music21
import decimal
import fractions
import functools
import decimal
import numpy
import math

class Composition:
    
    
    def __init__(self, sieves, form=None):
        self.sieves = sieves
        self.period = None
        self.form = form if form is not None else 'Prime'
        self.binary = self.set_binary(sieves)
        self.changes = [[tupl[1] for tupl in sublist] for sublist in self.get_consecutive_count()]
        self.form = self.distribute_changes(self.changes)
        self.grids_set = self.set_grids()
        self.normalized_numerators = self.set_normalized_numerators()
        self.multipliers = self.get_least_common_multiple(self.normalized_numerators)
        self.ticks_per_beat = 480

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
        
        percent_of_period = [[(decimal.Decimal(num) / decimal.Decimal(self.period)) for num in l] for l in lst]
        
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


    def set_normalized_numerators(self):

        denominators = [fraction.denominator for sublist in self.grids_set for fraction in sublist]
        lcd = functools.reduce(math.lcm, denominators)
        multipliers = [lcd // fraction.denominator for sublist in self.grids_set for fraction in sublist]
    
        return numpy.array([multipliers[i] * fract.numerator
                for grid in self.grids_set
                for i, fract in enumerate(grid)])


    #######################
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

    lcm = comp.get_least_common_multiple(comp.normalized_numerators)

    # print([num / lcm for num in comp.normalized_numerators])

    print(numpy.array([lcm // num for num in comp.normalized_numerators]))

    # print(comp.grids_set)

    print(comp.binary)