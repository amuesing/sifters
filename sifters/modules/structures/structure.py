from modules.composition import Composition

import music21
import decimal
import fractions
import decimal
import math

class Structure(Composition):
    
    
    def __init__(self, sieves):
        self.period = None
        self.binary = self.get_binary(sieves)
        self.consecutive_changes = [[tupl[1] for tupl in sublist] for sublist in self.get_consecutive_count()]
        self.structure_list = self.distribute_changes(self.consecutive_changes)
        self.length_of_form = [sum(self.flatten_list(self.structure_list[i])) for i in range(len(self.structure_list))]
        self.grids = self.get_grids()


    def get_binary(self, sieves):
                
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

    
    def get_grids(self):
        
        percent = self.get_percent_of_period(self.consecutive_changes)
        
        grids = self.convert_decimal_to_fraction(percent)
        
        grids = self.get_unique_fractions(grids)
        
        # # Flatten the nested lists into a single list
        # flat_list = self.flatten_list(percent)
        
        # # Remove duplicates and get the unique values
        # unique_values = list(set(flat_list))
        
        # lcm = [self.lcm_of_decimals(lst) for lst in percent]
        
        return percent