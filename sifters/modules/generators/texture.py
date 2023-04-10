from modules.generators.composition import *
from modules.generators.utility import *

import music21
import fractions
import itertools
import decimal
import pandas
import numpy
import math

class Texture(Composition):
    '''
    A class representing a texture in a composition.
    
    Attributes:
        grid_history (list): A list of Fraction objects representing the history of grid values for all texture objects.
        texture_id (int): An integer representing the unique ID of the current texture.
        grid (Fraction): A Fraction object representing the current grid value for the texture.
        binary (list): A list of lists representing the binary form of the texture.
        intervals (list): A list of lists representing the indices of intervals in the binary form of the texture.
        period (int): An integer representing the period of the binary form of the texture.
        factors (list): A list of integers representing the factors of the period of the binary form of the texture.
    '''
    grid_history = []
    texture_id = 1
        
        
    def __init__(self, sivs, grid=None, form=None):
        '''
        Initializes a Texture object.
        
        Args:
            sivs (list): A list of lists representing the sieve(s) (set-class interval vectors) of the texture.
            grid (Fraction): A Fraction object representing the grid value for the texture (default: 1/1).
            form (str): A string representing the form of the texture to be used. Can be 'Prime', 'Inversion', 'Retrograde', or 'Retrograde-Inversion' (default: 'Prime').
        '''
        # Set the grid attribute of the Texture object
        self.grid = fractions.Fraction(grid) if grid is not None else fractions.Fraction(1, 1)
        
        # Set the form attribute of the Texture object
        self.form = form if form is not None else 'Prime'
        
        # Set the binary attribute of the Texture object
        self.binary = self.set_binary(sivs)
        
        # Set the intervals attribute of the Texture object
        self.intervals = self.find_indices(self.binary, 1)
        
        # Set the closed_intervals attribute of the Texture object
        self.closed_intervals = self.set_octave_interpolation(self.intervals)
        
        # Set the factors attribute of the Texture object
        self.factors = self.get_factors(self.period)
        
        # Add the current grid value to the grid history list
        self.grid_history.append(self.grid)
        
        # Set the texture ID attribute of the Texture object
        self.texture_id = Texture.texture_id
        
        # Increment the texture ID for the next Texture object
        Texture.texture_id += 1
        
        
    def set_binary(self, sivs):
        '''
        Transforms a list of sets of intervals into a list of their binary forms, based on a selected form.
        
        Args:
            sivs (List[List[int]]): A list of sets of intervals, where each set is a list of integers.
            
        Returns:
            List[List[int]]: A list of the binary forms for each input set of intervals.
        '''
        # Convert the list of sets of intervals to their binary forms
        binary = self.get_binary(sivs)
        
        # Define a dictionary with lambda functions to transform the binary forms into different forms
        forms = {
            'Prime': lambda bin: bin,
            'Inversion': lambda bin: [1 if x == 0 else 0 for x in bin],
            'Retrograde': lambda bin: bin[::-1],
            'Retrograde-Inversion': lambda bin: [1 if x == 0 else 1 for x in bin][::-1]
        }
        
        # Apply the selected form to each binary form in the list, and return the resulting list
        return [forms[self.form](bin) for bin in binary]
    
    
    def get_binary(self, sivs):
        '''
        Returns the binary representation of the input sieve(s).
        
        If a tuple of sieves is given, this function computes the binary representation
        of each sieve and returns them as a list. If a single sieve is given, it returns its
        binary representation as a list with a single element.
        
        Args:
            sivs: A single sieve or a tuple of sieves.
            
        Returns:
            A list of binary representations of the input sieve(s).
        '''
        binary = []
        
        # If the input is a tuple, compute the binary representation for each sieve.
        if isinstance(sivs, tuple):
            periods = []
            objects = []
            for siv in sivs:
                obj = music21.sieve.Sieve(siv)
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
            object = music21.sieve.Sieve(sivs)
            object.setZRange(0, object.period() - 1)
            binary.append(object.segment(segmentFormat='binary'))
            
        return binary
    
    
    def find_indices(self, binary_lists, target):
        '''
        Finds the indices of the target element in each binary list.
        
        Args:
            binary_lists (list): A list of binary lists.
            target (int): The target element.
            
        Returns:
            list: A list of lists, where each sublist contains the indices of the target element in the corresponding binary list.
        '''
        indices = []
        for i in range(len(binary_lists)):
            ind = []
            for j in range(len(binary_lists[i])):
                if binary_lists[i][j] == target:
                    ind.append(j)
            indices.append(ind)
        return indices
    
    
    @staticmethod
    def get_factors(num):
        '''
        Given a positive integer, returns a list of its factors.
        
        Args:
            num (int): a positive integer
        
        Returns:
            factors (list): a list of positive integers that are factors of num
        '''
        factors = []
        i = 1
        while i <= num:
            if num % i == 0:
                factors.append(i)
            i += 1
        return factors
    
    
    def get_least_common_multiple(self, nums):
        '''
        Finds the least common multiple of a list of numbers.
        
        Args:
            nums: A list of integers.
        
        Returns:
            The least common multiple of the given list of integers.
        '''
        if len(nums) == 2:
            return nums[0] * nums[1] // math.gcd(nums[0], nums[1])
        elif len(nums) > 2:
            middle = len(nums) // 2
            left_lcm = self.get_least_common_multiple(nums[:middle])
            right_lcm = self.get_least_common_multiple(nums[middle:])
            return left_lcm * right_lcm // math.gcd(left_lcm, right_lcm)
        else:
            return nums[0]
        
        
    def get_largest_prime_factor(self, num):
        '''
        Returns the largest prime factor of a given integer.
        
        Args:
            num (int): The integer to find the largest prime factor of
        
        Returns:
            The largest prime factor of the given integer
        '''
        # Iterate through all numbers up to the square root of num
        for i in range(1, int(num ** 0.5) + 1):
            # If i is a factor of num, check if num // i is prime
            if num % i == 0:
                factor = num // i
                if self.is_prime(factor):
                    return factor
                # If num // i is not prime, check if i is prime
                elif self.is_prime(i):
                    return i
        # If no prime factors are found, return num
        return num
    
    
    @staticmethod
    def is_prime(num):
        '''
        Check if a given number is prime.
        
        Args:
            num (int): The number to check.
            
        Returns:
            bool: True if the number is prime, False otherwise.
        '''
        if num < 2:
            return False
        for i in range(2, num):
            if num % i == 0:
                return False
        return True
    
    
    @staticmethod
    def set_octave_interpolation(intervals):
        '''
        Interpolates the given intervals into the range of 0 to 11.
        
        For each interval, the method generates a list of the same length containing the values of
        the given interval modulo 12. These lists are appended to a resulting list, and that list
        is returned.
        
        Args:
            intervals: a list of lists of integers representing musical intervals.
        
        Returns:
            list: A list of lists of integers representing musical intervals mapped to the range of 0 to 11.
        '''
        set = []
        mod12 = list(range(12))
        for i in intervals:
            siv = []
            for j in i:
                siv.append(mod12[j % len(mod12)])
            set.append(siv)
        return set
    
    
    @staticmethod
    def segment_octave_by_period(period):
        '''
        Returns a list of decimal intervals, equally spaced by the given period in the 12-tone octave.
        
        Args:
            period (int): The number of equally spaced intervals in the octave.
            
        Returns:
            list: A list of decimal intervals, equally spaced by the given period in the 12-tone octave.
        '''
        interval = decimal.Decimal('12') / decimal.Decimal(str(period))
        return [interval * decimal.Decimal(str(i)) for i in range(period)]
    
    
    @staticmethod
    def parse_pitch_data(dataframe):
        '''
        Parses the pitch data in the given dataframe, computing the 'Pitch' and 'MIDI' columns for each row.
        
        Args:
            dataframe (pandas.DataFrame): The dataframe to parse.
            
        Returns:
            pandas.DataFrame: The updated dataframe.
        '''
        # Compute 'Pitch' and 'MIDI' columns for each row
        for index, row in dataframe.iterrows():
            pitch = round(row['MIDI'] - math.floor(row['MIDI']), 4)
            midi = math.floor(row['MIDI'])
            dataframe.at[index, 'MIDI'] = midi
            dataframe.at[index, 'Pitch'] = pitch
        # Reorder the columns
        column_order = ['Velocity', 'MIDI', 'Pitch', 'Start', 'End']
        dataframe = dataframe.reindex(columns=column_order)
        # Return the updated dataframe
        return dataframe
    
    
    @staticmethod
    def get_successive_diff(lst):
        """
        Takes a list of integers and returns a list containing the difference between each successive integer.
        
        Args:
            list: A list of integers
            
        Returns:
            list: A list of integers representing the successive difference 
        """
        return [0] + [lst[i+1] - lst[i] for i in range(len(lst)-1)]
    
    
    def set_notes_data(self):
        '''
        Creates the notes_data DataFrame from the given texture data.
        
        For each binary form (self.binary), iterate over a list of factors (self.factors) and 
        append a list of notes data (notes_data) with cooresponding data for each note event.
            
        Returns:
            None
        '''
        notes_data = []  # A list container for notes_data.
        
        # Create an iterator which is equal to the length of a list of forms represented in binary.
        for i in range(len(self.binary)):
            
            # # Create a midi_pool for each sieve represented in self.binary.
            # midi_pool = itertools.cycle(self.generate_midi_pool(i))
            
            # Create an iterator which is equal to the length of a list of factors (for self.period).
            for j in range(len(self.factors)):
                
                # Create a midi_pool for each sieve represented in self.binary.
                midi_pool = itertools.cycle(self.generate_midi_pool(i, j))
                # mid = self.generate_midi_pool(i, j)
                
                # Repeat form a number of times sufficient to normalize pattern length against sieves represented in self.binary.
                pattern = numpy.tile(self.binary[i], self.factors[j])
                
                # Create a list of indices where non-zero elements occur within the pattern.
                indices = numpy.nonzero(pattern)[0]
                # print(len(mid))
                print(f'indices {len(indices)}')
                
                # Find the multiplier for self.grid to normalize duration length against number of repititions of sieve in pattern.
                duration_multiplier = self.period / self.factors[j]
                
                # Find the duration of each note represented as a float.
                duration = self.grid * duration_multiplier
                
                # For each non-zero indice append notes_data list with corresponding midi information.
                for k in indices:
                    velocity = 127
                    offset = k * duration
                    notes_data.append([velocity, next(midi_pool), offset, offset + self.grid])
                    
        notes_data = [[data[0], data[1], round(data[2], 6), round(data[3], 6)] for data in notes_data]
        
        self.notes_data = pandas.DataFrame(notes_data, columns=['Velocity', 'MIDI', 'Start', 'End']).sort_values(by='Start').drop_duplicates()
    
    
    def generate_midi_pool(self, binary_index, factor_index):
        '''
        Generates a MIDI pool for a given sieve represented in self.binary.
        The MIDI pool is constructed by computing the interval list for a given sieve, 
        creating a pitch matrix based on the intervals in the sieve, and generating all possible
        combinations of the rows and columns in the matrix.
        
        Args:
            binary_index (int): Index representing the i loop from set_notes_data method. 
                                Iterates over binary form in self.binary.
            factor_index (int): Index representing the j loop from set_notes_data method. 
                                Iterates over factor in self.factors.
        
        Returns:
            A list of MIDI values for the given sieve.
        '''
        # Set the base tonality value.
        tonality = 40
        
        # Given a set number of events, and a set number of rotations, how can we order pitch selection
        # based on the logic of the sieve?
        num_of_events = (len(self.closed_intervals[binary_index]) * self.factors[factor_index])
        num_of_positions = num_of_events // len(self.closed_intervals[binary_index])
        
        # Compute the starting pitch for the sieve.
        first_pitch = tonality + self.closed_intervals[binary_index][0]
        
        # Get the indices of non-zero elements in the sieve.
        indices = numpy.nonzero(self.binary[binary_index])[0]
        
        # Get the intervals associated with the non-zero elements.
        segment = self.segment_octave_by_period(self.period)
        intervals = [segment[i] for i in indices]
        
        steps = self.get_successive_diff(self.closed_intervals[binary_index])
        
        # Generate a pitch matrix based on the intervals.
        matrix = first_pitch + Composition.generate_pitchclass_matrix(intervals)
        
        # Retrograde every time the intervals traverse the range of the matrix and repeat?
        print(f'events {num_of_events}')
        pool = []
        rotations = num_of_events // len(steps)
        current_index = 0
        retrograde = False
        # for _ in range(rotations):
        for step in steps:
            wrapped_index = (current_index + abs(step)) % len(self.intervals[binary_index])
            # What if there are more than 1 cycles-- False -> True -> False?
            # print(abs(step) + current_index)
            # print(len(self.intervals[binary_index]))
            if (abs(step) + current_index) >= len(self.intervals[binary_index]):
                if retrograde == False:
                    retrograde = True
                else:
                    retrograde = False
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
        flattened_pool = [num for list in pool for num in list]
        print(f'pool {len(flattened_pool)}')
        return flattened_pool
    
    
class NonPitched(Texture):
    '''
    A class representing a non-pitched instrument in a musical texture.
    
    Attributes:
        part_id (int): The ID value of the instrument.
        name (str): The name of the instrument.
    '''
    # Initialize ID for the first instance of NonPitched object.
    part_id = 1
    
    def __init__(self, sivs, grid=None, form=None):
        '''
        Initializes a NonPitched instrument with specified sieves, grid, MIDI mapping and form.
        
        Args:
            sivs: A single sieve or a tuple of sieves representing the pitch content of the instrument.
            grid: A Grid object representing the rhythmic content of the instrument (optional).
            form: A Form object representing the formal structure of the instrument (optional).
        '''
        super().__init__(sivs, grid, form)
        
        # Set name of the instrument as "NonPitched".
        self.name = 'NonPitched'
        
        # Set unique ID value for the instrument.
        self.part_id = NonPitched.part_id
        
        # Increment ID value for next instance.
        NonPitched.part_id += 1
        
        # Create a part for the instrument in the musical texture.
        self.set_notes_data()
        
        # Add a Pitch column to the dataframe which seperates and tracks the decimal from the MIDI column values.
        self.notes_data = self.parse_pitch_data(self.notes_data)
    
    
class Monophonic(Texture):
    # Initialize ID value for first instance of Monophonic object.
    part_id = 1
    
    def __init__(self, sivs, grid=None, form=None):
        '''
        Initializes a Monophonic instrument.
        
        Args:
            sivs (int or tuple): The generative sieve(s) of the texture.
            grid (float, optional): The grid size for the part. Defaults to None.
            midi (list, optional): A list of MIDI pitches to be used for creating the part. Defaults to None.
            form (list, optional): The form of the texture. Defaults to None.
        '''
        # Call superclass constructor.
        super().__init__(sivs, grid, form)
        
        # Set name of instrument.
        self.name = 'Monophonic'
        
        # Set ID value.
        self.part_id = Monophonic.part_id
        
        # Increment ID value.
        Monophonic.part_id += 1
        
        # Create a part for the instrument in the musical texture.
        self.set_notes_data()
        
        # Group notes with the same start time into a single note with the highest MIDI value.
        self.notes_data = self.group_by_start(self.notes_data)
        
        # Get the lowest MIDI note for each start time.
        self.notes_data = self.get_lowest_midi(self.notes_data)
        
        # Close the intervals by transposing all notes to the lowest octave containing the notes.
        self.notes_data = self.close_intervals(self.notes_data)
        
        # Combine consecutive MIDI values with the same start time into a single note with a longer duration.
        self.notes_data = self.combine_consecutive_midi_values(self.notes_data)
        
        # Convert lists of pitch data into scalar pitch data.
        self.notes_data = self.convert_lists_to_scalars(self.notes_data)
        
        # Add a Pitch column to the dataframe which seperates and tracks the decimal from the MIDI column values.
        self.notes_data = self.parse_pitch_data(self.notes_data)
        
    # How to use the referenced sieve to select row form?
    # How to use number of needed events to generate exactly the correct amount of pitch data needed?
    # What about using the set_binary method to determine row selection?
    # How to have a single generate_midi_pool method for all texture classes?