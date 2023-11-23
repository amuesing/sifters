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
        self.intervals = [i for i in range(len(self.binary)) if self.binary[i] == 1]
        
        # Derive modular-12 values from self.intervals. 
        mod12 = list(range(12))
        self.closed_intervals = [mod12[i % len(mod12)] for i in self.intervals]
        
        # Set the factors attribute of the Texture object
        self.factors = [i for i in range(1, self.period + 1) if self.period % i == 0]
        
        # self.set_notes_data()

        Texture.texture_id += 1


    def get_successive_diff(self, lst):
        return [0] + [lst[i+1] - lst[i] for i in range(len(lst)-1)]
    
    
    def segment_octave_by_period(self, period):
        interval = decimal.Decimal('12') / decimal.Decimal(str(period))
        return [interval * decimal.Decimal(str(i)) for i in range(period)]
    
    
    def generate_pitchclass_matrix(self, intervals):
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


    def generate_note_pool_from_matrix(self, matrix, num_of_positions, steps_cycle):
        pool = []
        current_index = 0
        retrograde = False

        for _ in range(num_of_positions):
            step = next(steps_cycle)
            wrapped_index = (current_index + abs(step)) % len(self.intervals)
            wrap_count = (abs(step) + current_index) // len(self.intervals)

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
            steps = self.get_successive_diff(self.closed_intervals)
            steps_cycle = itertools.cycle(steps)
            first_pitch = tonality + self.closed_intervals[0]
            indices = numpy.nonzero(self.binary)[0]
            segment = self.segment_octave_by_period(self.period)
            intervals = [segment[i] for i in indices]
            matrix = first_pitch + self.generate_pitchclass_matrix(intervals)
            num_of_events = (len(self.closed_intervals) * self.factors[factor_index])
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


    def create_dataframe(self, notes_data):
        columns = ['texture_id', 'Start', 'Velocity', 'Note', 'Duration']
        dataframe = pandas.DataFrame(notes_data, columns=columns)
        dataframe = dataframe.sort_values(by='Start').drop_duplicates().reset_index(drop=True)
        dataframe = dataframe.apply(pandas.to_numeric, errors='ignore')
        return dataframe


    def insert_texture_into_database(self):
        cursor = self.mediator.connection.cursor()
        cursor.execute("INSERT INTO textures (name) VALUES (?)", (self.__class__.__name__,))


    def insert_notes_into_database(self, dataframe):
        dataframe.to_sql(name='notes', con=self.mediator.connection, if_exists='append', index=False)
        dataframe.to_csv(f'data/csv/.{self.__class__.__name__}.csv')
        
        
    def set_notes_data(self):
        notes_data = self.generate_notes_data()
        dataframe = self.create_dataframe(notes_data)
        self.insert_texture_into_database(dataframe)
        self.insert_notes_into_database(dataframe)

    ########################################################################################################
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
        for i in range(len(dataframe)):
            current_row = dataframe.loc[i]

            if len(current_row['Note']) > 1:
                min_note_index = current_row['Note'].index(min(current_row['Note']))
                selected_note_value = current_row['Note'][min_note_index]
                dataframe.loc[i, 'Note'] = [selected_note_value]
                dataframe.loc[i, 'Velocity'] = [current_row['Velocity'][min_note_index]]
                # dataframe.loc[i, 'Duration'] = [current_row['Duration'][min_note_index]]

            if i < len(dataframe) - 1:
                next_row = dataframe.loc[i + 1]

                if len(current_row['Note']) == 1 and len(next_row['Note']) > 1:
                    current_note = current_row['Note'][0]
                    next_note_values = next_row['Note']
                    closest_note = min(next_note_values, key=lambda x: abs(x - current_note))
                    dataframe.loc[i + 1, 'Note'] = [closest_note]
                    dataframe.loc[i + 1, 'Velocity'] = next_row['Velocity'][next_note_values.index(closest_note)]
                    # dataframe.loc[i + 1, 'Duration'] = next_row['Duration'][next_note_values.index(closest_note)]

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
                if (dataframe.loc[i, 'End'] + dataframe.loc[i, 'Duration']) < dataframe.loc[i + 1, 'Start']:
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