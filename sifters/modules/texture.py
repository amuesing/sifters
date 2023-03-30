from modules.composition import *

import music21
import fractions
import itertools
import decimal
import pandas
import numpy
import math

class Texture(Composition):
    """
    A class representing a texture in a composition.

    Attributes:
        grid_history (list): A list of Fraction objects representing the history of grid values for all textures.
        texture_id (int): An integer representing the unique ID of the current texture.
        grid (Fraction): A Fraction object representing the current grid value for the texture.
        midi (list): A list of integers representing MIDI note numbers for the texture.
        form (list): A list of lists representing the binary form of the texture.
        intervals (list): A list of lists representing the indices of intervals in the binary form of the texture.
        period (int): An integer representing the period of the binary form of the texture.
        factors (list): A list of integers representing the factors of the period of the binary form of the texture.
    """
    grid_history = []
    texture_id = 1
        
    def __init__(self, sivs, grid=None, midi=None, form=None):
        """
        Initializes a Texture object.

        Args:
            sivs (list): A list of lists representing the SIVs (set-class interval vectors) of the texture.
            grid (Fraction): A Fraction object representing the grid value for the texture (default: 1/1).
            midi (list): A list of integers representing MIDI note numbers for the texture (default: [45, 46, 47, 48, 49]).
            form (str): A string representing the form of the texture to be used. Can be 'Prime', 'Inversion', 'Retrograde', or 'Retrograde-Inversion' (default: 'Prime').
        """
        self.grid = fractions.Fraction(grid) if grid is not None else fractions.Fraction(1, 1)
        self.midi = midi if midi is not None else [45, 46, 47, 48, 49]
        self.form = self.select_form(sivs, form if form is not None else 'Prime')
        self.intervals = self.find_indices(self.form, 1)
        self.period = len(self.form[0])
        self.factors = self.get_factors(self.period) 
        self.grid_history.append(self.grid)
        self.texture_id = Texture.texture_id
        Texture.texture_id += 1

        
    def select_form(self, sivs, form):
        """
        Select a form of a set of intervals.
        
        Args:
            sivs (List[List[int]]): A list of sets of intervals.
            form (str): A string indicating the form to select. Must be one of
                'Prime', 'Inversion', 'Retrograde', or 'Retrograde-Inversion'.
            
        Returns:
            List[List[int]]: A list of the selected forms for each input set of intervals.
        """
        binary = self.get_binary(sivs)
        forms = {
            'Prime': lambda bin: bin,
            'Inversion': lambda bin: [1 if x == 0 else 0 for x in bin],
            'Retrograde': lambda bin: bin[::-1],
            'Retrograde-Inversion': lambda bin: [1 if x == 0 else 0 for x in bin][::-1]
        }
        return [forms[form](bin) for bin in binary]
    
    
    def find_indices(self, binary_lists, target):
        """
        Finds the indices of the target element in each binary list.
        
        Args:
            binary_lists (list): A list of binary lists.
            target (int): The target element.
            
        Returns:
            list: A list of lists, where each sublist contains the indices of the target element in the corresponding binary list.
        """
        indexes = []
        for i in range(len(binary_lists)):
            ind = []
            for j in range(len(binary_lists[i])):
                if binary_lists[i][j] == target:
                    ind.append(j)
            indexes.append(ind)
        return indexes
    
    
    @staticmethod
    def get_factors(num):
        """
        Given a positive integer, returns a list of its factors.
        
        Args:
            num (int): a positive integer
        
        Returns:
            factors (list): a list of positive integers that are factors of num
        """
        factors = []
        i = 1
        while i <= num:
            if num % i == 0:
                factors.append(i)
            i += 1
        return factors
    
    
    def get_binary(self, sivs):
        """
        Returns the binary representation of the input sieve(s).
        
        If a tuple of sieves is given, this function computes the binary representation
        of each sieve and returns them as a list. If a single sieve is given, it returns its
        binary representation as a list with a single element.
        
        Args:
            sivs: A single sieve or a tuple of sieves.
            
        Returns:
            A list of binary representations of the input sieve(s).
        """
        binary = []
        
        # If the input is a tuple, compute the binary representation for each SIV
        if isinstance(sivs, tuple):
            periods = []
            objects = []
            for siv in sivs:
                obj = music21.sieve.Sieve(siv)
                objects.append(obj)
                periods.append(obj.period())
                
            # Compute the least common multiple of the periods of the input SIVs
            lcm = self.get_least_common_multiple(periods)
            
            # Set the Z range of each SIV object and append its binary representation to the list
            for obj in objects:
                obj.setZRange(0, lcm - 1)
                binary.append(obj.segment(segmentFormat='binary'))
        else:
            # Compute the binary representation for the single input SIV
            object = music21.sieve.Sieve(sivs)
            object.setZRange(0, object.period() - 1)
            binary.append(object.segment(segmentFormat='binary'))
            
        return binary
    
    
    def get_least_common_multiple(self, nums):
        """
        Finds the least common multiple of a list of numbers.
        
        Args:
            nums: A list of integers.
        
        Returns:
            The least common multiple of the given list of integers.
        """
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
        """
        Returns the largest prime factor of a given integer.
        
        Args:
            num (int): The integer to find the largest prime factor of
        
        Returns:
            The largest prime factor of the given integer
        """
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
        """
        Check if a given number is prime.
        
        Args:
            num (int): The number to check.
            
        Returns:
            bool: True if the number is prime, False otherwise.
        """
        if num < 2:
            return False
        for i in range(2, num):
            if num % i == 0:
                return False
        return True
    
    
    @staticmethod
    def octave_interpolation(intervals):
        """
        Interpolates the given intervals into the range of 0 to 11.
        
        For each interval, the method generates a list of the same length containing the values of
        the given interval modulo 12. These lists are appended to a resulting list, and that list
        is returned.
        
        Args:
            intervals: a list of lists of integers representing musical intervals.
        
        Returns:
            list: A list of lists of integers representing musical intervals mapped to the range of 0 to 11.
        """
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
        """
        Returns a list of decimal intervals, equally spaced by the given period in the 12-tone octave.

        Args:
            period (int): The number of equally spaced intervals in the octave.

        Returns:
            list: A list of decimal intervals, equally spaced by the given period in the 12-tone octave.
        """
        interval = decimal.Decimal('12') / decimal.Decimal(str(period))
        return [interval * decimal.Decimal(str(i)) for i in range(period)]

    
    @staticmethod
    def parse_pitch_data(dataframe):
        """
        Parses the pitch data in the given dataframe, computing the 'Pitch' and 'MIDI' columns for each row.
        
        Args:
            dataframe (pandas.DataFrame): The dataframe to parse.
            
        Returns:
            pandas.DataFrame: The updated dataframe.
        """
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
    
    
class NonPitched(Texture):
    part_id = 1 # First instance has ID of 1.
    
    def __init__(self, sivs, grid=None, midi=None, form=None):
        super().__init__(sivs, grid, midi, form)
        self.name = 'NonPitched' # Set name of instrument.
        self.part_id = NonPitched.part_id # Set ID value.
        NonPitched.part_id += 1 # Increment ID value.
        self.create_part()
        
    def create_part(self):
        notes_data = []
        for i in range(len(self.form)):
            midi_pool = itertools.cycle(self.midi_pool(i))
            for j in range(len(self.factors)):
                pattern = numpy.tile(self.form[i], self.factors[j])
                indices = numpy.nonzero(pattern)[0]
                duration = self.grid * (self.period / self.factors[j])
                for k in indices:
                    velocity = 127
                    offset = k * duration
                    notes_data.append([velocity, next(midi_pool), offset, offset + self.grid])
        notes_data = [[data[0], data[1], round(data[2], 6), round(data[3], 6)] for data in notes_data]
        self.notes_data = pandas.DataFrame(notes_data, columns=['Velocity', 'MIDI', 'Start', 'End']).sort_values(by = 'Start').drop_duplicates()
        
    def midi_pool(self, index):
        events = self.form[index].count(1)
        largest_prime_slice = slice(0, self.get_largest_prime_factor(events))
        pool = itertools.cycle(self.midi[largest_prime_slice])
        return [next(pool) for _ in range(events)]
    
class Monophonic(Texture):
    part_id = 1 # First instance has ID of 1.
    
    def __init__(self, sivs, grid=None, midi=None, form=None):
        super().__init__(sivs, grid, midi, form)
        self.name = 'Monophonic' # Set name of texture.
        self.part_id = Monophonic.part_id # Set ID value.
        Monophonic.part_id += 1 # Increment ID value.
        self.closed_intervals = self.octave_interpolation(self.intervals) # Contain all intervals within a mod12 continuum. 
        self.create_part() # Call the create_Texture method.
        
    def create_part(self):
        notes_data = [] # A list container for notes_data.
        for i in range(len(self.form)): # Set an iterator for each sieve represented in self.form.
            # midi_pool = itertools.cycle(self.midi_pool(i)) # Create a midi_pool for each sieve represented in self.form.
            midi_pool = itertools.cycle(self.generate_midi_pool(i))
            for j in range(len(self.factors)): # Set an iterator for each sieve based on the factorization of self.period.
                pattern = numpy.tile(self.form[i], self.factors[j]) # Repeat form a number of times sufficient to normalize pattern length against sieves represented in self.form.
                indices = numpy.nonzero(pattern)[0] # Create a list of indicies where non-zero elements occur within the pattern.
                multiplier = self.period / self.factors[j] # Find the number of repititions required to achieve periodicity per sieve represented in self.form.
                duration = self.grid * multiplier # Find the duration of each note represented as a float.
                for k in indices: # For each non-zero indice append notes_data list with cooresponding midi information.
                    velocity = 127
                    offset = k * duration
                    notes_data.append([velocity, next(midi_pool), offset, offset + self.grid])
        notes_data = [[data[0], data[1], round(data[2], 6), round(data[3], 6)] for data in notes_data]
        self.notes_data = pandas.DataFrame(notes_data, columns=['Velocity', 'MIDI', 'Start', 'End']).sort_values(by = 'Start').drop_duplicates()
        self.notes_data = self.group_by_start(self.notes_data)
        self.notes_data = self.get_lowest_midi(self.notes_data)
        self.notes_data = self.close_intervals(self.notes_data)
        self.notes_data = self.combine_consecutive_midi_values(self.notes_data)
        self.notes_data = self.convert_lists_to_scalars(self.notes_data)
        self.notes_data = self.parse_pitch_data(self.notes_data)
        
    # How to use the referenced sieve to select row form?
    # How to use number of needed events to generate exactly the correct amount of pitch data needed?
    # midi_pool represents a sequence of pitch data that is repeated until the required number of notes needed has been satisfied.
    # How does the number of needed notes relate to the pool data? How does the pool data relate to the matrix of intervals?
    # What about using the select_form method to determine row selection?
    
    def generate_midi_pool(self, form_index):
        tonality = 40
        pitch = tonality + self.closed_intervals[form_index][0]
        indices = numpy.nonzero(self.form[form_index])[0]
        segment = self.segment_octave_by_period(self.period)
        intervals = [segment[i] for i in indices]
        matrix = pitch + Composition.generate_pitchclass_matrix(intervals)
        combo = [matrix.iloc[i].values.tolist() for i, _ in enumerate(matrix)] + [matrix.iloc[:, i].values.tolist() for i, _ in enumerate(matrix)]
        pool = list(itertools.chain(*combo))
        return pool
    
# Monophonic
# Homophonic
# Polyphonic
# Heterophonic