import itertools
import decimal
import pandas
import numpy


class Texture:
        
    def __init__(self, source_data, database_connection):

        # Initialize an instance of the Utility class to call helper methods from.
        self.database_connection = database_connection
        
        self.binary = source_data

        self.period = len(self.binary)

        # Find all occurences of 1 and derive an intervalic structure based on their indices.
        self.intervals = [i for i in range(len(self.binary)) if self.binary[i] == 1]
        
        # Derive modular-12 values from self.intervals. 
        mod12 = list(range(12))
        self.closed_intervals = [mod12[i % len(mod12)] for i in self.intervals]
        
        # Set the factors attribute of the Texture object
        self.factors = [i for i in range(1, self.period + 1) if self.period % i == 0]
        
        self.notes_data = self.set_notes_data()

        self.notes_data.to_csv(f'data/csv/.{self.__class__.__name__}.csv')


    def _get_successive_diff(self, lst):
        return [0] + [lst[i+1] - lst[i] for i in range(len(lst)-1)]
    
    
    def _segment_octave_by_period(self, period):
        interval = decimal.Decimal('12') / decimal.Decimal(str(period))
        return [interval * decimal.Decimal(str(i)) for i in range(period)]
    
    
    def _generate_pitchclass_matrix(self, intervals):

        # Calculate the interval between each pair of consecutive pitches.
        next_interval = intervals[1:]
        row = [decimal.Decimal('0.0')] + [next_interval[i] - intervals[0] for i, _ in enumerate(intervals[:-1])]

        # Normalize the tone row so that it starts with 0 and has no negative values.
        row = [note % 12 for note in row]

        # Generate the rows of the pitch class matrix.
        matrix = [[(abs(note - 12) % 12)] for note in row]

        # Generate the columns of the pitch class matrix.
        matrix = [row * len(intervals) for row in matrix]

        # Update the matrix with the correct pitch class values.
        matrix = [[(matrix[i][j] + row[j]) % 12
                for j, _ in enumerate(range(len(row)))]
                for i in range(len(row))]

        # Label the rows and columns of the matrix.
        matrix = pandas.DataFrame(matrix,
                                index=[f'P{m[0]}' for m in matrix], 
                                columns=[f'I{i}' for i in matrix[0]])

        return matrix


    def _generate_note_pool(self, factor_index):
        
        # Set the base tonality value.
        tonality = decimal.Decimal(40.0)
        
        # Generate a list of successieve differences between the intervals.
        steps = self._get_successive_diff(self.closed_intervals)

        # Create a cycle iterator for the steps list.
        steps_cycle = itertools.cycle(steps)
        
        # Compute the starting pitch for the sieve.
        first_pitch = tonality + self.closed_intervals[0]

        # Get the indices of non-zero elements in the sieve.
        indices = numpy.nonzero(self.binary)[0]
        
        # Get the intervals associated with the non-zero elements.
        segment = self._segment_octave_by_period(self.period)
        intervals = [segment[i] for i in indices]
        
        # Generate a pitch matrix based on the intervals.
        matrix = first_pitch + self._generate_pitchclass_matrix(intervals)

        # Compute the number of events and positions needed for the sieve.
        num_of_events = (len(self.closed_intervals) * self.factors[factor_index])
        num_of_positions = num_of_events // len(steps)

        # Generate the note pool by iterating through the steps and matrix.
        pool = []
        current_index = 0
        retrograde = False
        for _ in range(num_of_positions):
            step = next(steps_cycle)
            wrapped_index = (current_index + abs(step)) % len(self.intervals)

            # Check if the intervals have wrapped around the range of the matrix.
            wrap_count = (abs(step) + current_index) // len(self.intervals)
            
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
    
    
    def set_notes_data(self):
        
        # Create a list container for notes_data.
        notes_data = []
        
        for factor_index in range(len(self.factors)):

            note_pool = itertools.cycle(self._generate_note_pool(factor_index))

            # Repeat form a number of times sufficient to normalize pattern length against sieves represented in self.binary.
            pattern = numpy.tile(self.binary, self.factors[factor_index])
            
            # Create a list of indices where non-zero elements occur within the pattern.
            indices = numpy.nonzero(pattern)[0]
            
            duration = self.period // self.factors[factor_index]

            # For each non-zero indice append notes_data list with corresponding note information.
            for index in indices:
                velocity = 64
                start = index * duration

                notes_data.append((start, velocity, next(note_pool), duration))

        return pandas.DataFrame(notes_data, columns=['Start', 'Velocity', 'Note', 'Duration']).sort_values(by='Start').drop_duplicates().reset_index(drop=True)


    # @staticmethod
    # def get_closest_note(dataframe):
        
    #     # Iterate over the dataframe rows
    #     for i in range(len(dataframe)):
    #         current_row = dataframe.loc[i]

    #         if len(current_row['Note']) > 1:
    #             min_note_index = current_row['Note'].index(min(current_row['Note']))
    #             selected_note_value = current_row['Note'][min_note_index]
    #             dataframe.loc[i, 'Note'] = [selected_note_value]
    #             dataframe.loc[i, 'Velocity'] = [current_row['Velocity'][min_note_index]]
    #             # dataframe.loc[i, 'Duration'] = [current_row['Duration'][min_note_index]]

    #         if i < len(dataframe) - 1:
    #             next_row = dataframe.loc[i + 1]

    #             if len(current_row['Note']) == 1 and len(next_row['Note']) > 1:
    #                 current_note = current_row['Note'][0]
    #                 next_note_values = next_row['Note']
    #                 closest_note = min(next_note_values, key=lambda x: abs(x - current_note))
    #                 dataframe.loc[i + 1, 'Note'] = [closest_note]
    #                 dataframe.loc[i + 1, 'Velocity'] = next_row['Velocity'][next_note_values.index(closest_note)]
    #                 # dataframe.loc[i + 1, 'Duration'] = next_row['Duration'][next_note_values.index(closest_note)]

    #     # Print the updated dataframe
    #     return dataframe
    

    # # If I run check_and_close_intervals I will get values that are too low or too high. (negative numbers)
    # def check_and_close_intervals(self, dataframe):
        
    #     for i in range(len(dataframe['Note']) - 1):
    #         if abs(dataframe['Note'][i] - dataframe['Note'][i + 1]) > 6: 
    #             dataframe = self.close_intervals(dataframe)
    #             return self.check_and_close_intervals(dataframe)
            
    #     return dataframe
    
    
    # @staticmethod
    # def close_intervals(dataframe):
        
    #     # Make a copy of the input dataframe.
    #     updated_dataframe = dataframe.copy()
        
    #     # Iterate through each pair of consecutive note values.
    #     for i, note in enumerate(updated_dataframe['Note'][:-1]):
    #         next_note = updated_dataframe['Note'][i + 1]
            
    #         # If the increase between note notes is greater than a tritone, transpose
    #         # the next note note up one octave.
    #         if note - next_note > 6:
    #             updated_dataframe.at[i + 1, 'Note'] = next_note + 12
            
    #         # If the decrease between note notes is greater than a tritone, transpose
    #         # the next note note down one octave.
    #         elif note - next_note < -6:
    #             updated_dataframe.at[i + 1, 'Note'] = next_note - 12
        
    #     # Return the updated dataframe.
    #     return updated_dataframe
    
        
    # @staticmethod
    # def adjust_note_range(dataframe):
        
    #     # Define the lambda function to adjust values outside the range [36, 60].
    #     adjust_value = lambda x: x - 12 if x > 60 else (x + 12 if x < 36 else x)
        
    #     # Apply the lambda function repeatedly until all values satisfy the condition.
    #     while dataframe['Note'].apply(lambda x: x < 36 or x > 60).any():
    #         dataframe['Note'] = dataframe['Note'].apply(adjust_value)
            
    #     return dataframe
    
    
    # @staticmethod
    # def combine_consecutive_note_values(dataframe):
    
    #     i = 0
    #     while i < len(dataframe) - 1:
    #         if dataframe.loc[i, 'Note'] == dataframe.loc[i + 1, 'Note']:
    #             if (dataframe.loc[i, 'Emd'] + dataframe.loc[i, 'Duration']) < dataframe.loc[i + 1, 'Start']:
    #                 i += 1
    #             else:
    #                 dataframe.loc[i, 'Duration'] += dataframe.loc[i + 1, 'Duration']
    #                 dataframe = dataframe.drop(i + 1).reset_index(drop=True)
    #         else:
    #             i += 1

    #     return dataframe
    
    
    # @staticmethod
    # def convert_lists_to_scalars(dataframe):
        
    #     # Iterate over each column in the dataframe
    #     for col in dataframe.columns:
    #         # Check if the column contains objects (lists or tuples)
    #         if dataframe[col].dtype == object:
    #             # Apply a lambda function to each value in the column
    #             # If the value is a list or tuple of length 1, replace it with the single value
    #             dataframe[col] = dataframe[col].apply(lambda x: x[0] if isinstance(x, (list, tuple)) else x)
        
    #     return dataframe