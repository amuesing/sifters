import decimal
import pandas

class Composition:
    def generate_pitchclass_matrix(intervals):
        '''
        Generate a pitch class matrix from a list of integers.
        
        The matrix is based on the concept of a twelve-tone row, a sequence of the twelve
        pitch classes in the chromatic scale, arranged in a particular order. The matrix
        displays the pitch classes in the order they appear in the input list, with each
        row representing a different pitch class.
        
        Args:
            intervals (list of int): A list of integers representing pitch intervals.
            
        Returns:
            pandas.DataFrame: A pitch class matrix, with rows labeled P0-P11 and columns
            labeled I0-I(n-1), where n is the number of intervals in the input list.
        '''
        
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
    
    
    @staticmethod
    def group_by_start(dataframe):
        '''
        Groups the input dataframe by the 'Start' column and returns the unique values for
        each column for each start time.
        
        Args:
            dataframe (pandas.DataFrame): The dataframe to group.
        
        Returns:
            pandas.DataFrame: A new dataframe containing the grouped data.
        '''
        
        # Group the notes_data dataframe by the 'Start' column and return the unique values
        # for each column for each start time.
        grouped_velocity = dataframe.groupby('Start')['Velocity'].apply(lambda x: sorted(set(x)))
        grouped_midi = dataframe.groupby('Start')['MIDI'].apply(lambda x: sorted(set(x)))
        grouped_end = dataframe.groupby('Start')['End'].apply(lambda x: sorted(set(x)))
        
        # If the 'Pitch' column exists in the dataframe, group it by 'Start' and get the unique values.
        if 'Pitch' in dataframe.columns:
            grouped_pitch = dataframe.groupby('Start')['Pitch'].apply(lambda x: sorted(set(x)))
            # Concatenate the grouped data into a new dataframe, and re-order the columns.
            result = pandas.concat([grouped_velocity, grouped_midi, grouped_pitch, grouped_end], axis=1).reset_index()
            result = result[['Velocity', 'MIDI', 'Pitch', 'Start', 'End']]
        else:
            # Concatenate the grouped data into a new dataframe, and re-order the columns.
            result = pandas.concat([grouped_velocity, grouped_midi, grouped_end], axis=1).reset_index()
            result = result[['Velocity', 'MIDI', 'Start', 'End']]
        
        # Return the result dataframe.
        return result
    
    @staticmethod
    def get_lowest_midi(dataframe):
        '''
        For each row in the input dataframe, select the lowest MIDI value in the 'MIDI' column.
        Drop any rows where the 'MIDI' value is None.
        
        Args:
            dataframe (pandas.DataFrame): Input dataframe.
            
        Returns:
            pandas.DataFrame: Output dataframe with the 'MIDI' column reduced to the lowest value in each row.
        '''
        dataframe['MIDI'] = dataframe['MIDI'].apply(lambda x: min(x) if x else None)
        dataframe = dataframe.dropna(subset=['MIDI'])
        if 'Pitch' in dataframe.columns:
            return dataframe[['Velocity', 'MIDI', 'Pitch', 'Start', 'End']]
        else:
            return dataframe[['Velocity', 'MIDI', 'Start', 'End']]
        
    def check_and_close_intervals(self, dataframe):
        '''
        Recursively check the intervals between adjacent MIDI values in the 'MIDI' column of the input dataframe.
        If the interval is greater than 6, apply the 'close_intervals' method to merge the intervals.
        
        Args:
            dataframe (pandas.DataFrame): Input dataframe.
            
        Returns:
            pandas.DataFrame: Output dataframe with adjacent intervals less than or equal to 6 merged.
        '''
        for i in range(len(dataframe['MIDI']) - 1):
            if abs(dataframe['MIDI'][i] - dataframe['MIDI'][i + 1]) > 6: 
                dataframe = self.close_intervals(dataframe)
                return self.check_and_close_intervals(dataframe)
        return dataframe
    
    @staticmethod
    def close_intervals(dataframe):
        '''
        Adjust the MIDI values in the dataframe to ensure that the interval between each
        pair of consecutive MIDI values is no greater than a tritone (six semitones).
        
        Args:
            dataframe (pandas.DataFrame): A dataframe containing MIDI data.
            
        Returns:
            pandas.DataFrame: A copy of the input dataframe, with the MIDI values adjusted as necessary.
        '''
        
        # Make a copy of the input dataframe.
        updated_df = dataframe.copy()
        
        # Iterate through each pair of consecutive MIDI values.
        for i, midi in enumerate(updated_df["MIDI"][:-1]):
            next_midi = updated_df["MIDI"][i + 1]
            
            # If the increase between midi notes is greater than a tritone, transpose
            # the next midi note up one octave.
            if midi - next_midi > 6:
                updated_df.at[i + 1, "MIDI"] = round(next_midi + 12, 3)
            
            # If the decrease between midi notes is greater than a tritone, transpose
            # the next midi note down one octave.
            elif midi - next_midi < -6:
                updated_df.at[i + 1, "MIDI"] = round(next_midi - 12, 3)
        
        # Return the updated dataframe.
        return updated_df
    
    @staticmethod
    def adjust_midi_range(dataframe):
        '''
        Adjust the MIDI values in a dataframe to ensure they are within the range [36, 60].
        
        Args:
            dataframe (pandas.DataFrame): Input dataframe.
            
        Returns:
            pandas.DataFrame: Output dataframe with MIDI values adjusted to be within the range [36, 60].
        '''
        # Define the lambda function to adjust values outside the range [36, 60].
        adjust_value = lambda x: x - 12 if x > 60 else (x + 12 if x < 36 else x)
        
        # Apply the lambda function repeatedly until all values satisfy the condition.
        while dataframe['MIDI'].apply(lambda x: x < 36 or x > 60).any():
            dataframe['MIDI'] = dataframe['MIDI'].apply(adjust_value)
            
        return dataframe
    
    @staticmethod
    def combine_consecutive_midi_values(dataframe):
        '''
        Combine consecutive MIDI notes in the input dataframe that have the same MIDI value and optional 'Pitch' value.
        
        Args:
            dataframe (pandas.DataFrame): Input dataframe.
            
        Returns:
            pandas.DataFrame: Output dataframe with consecutive MIDI notes combined.
        '''
        # Check if the dataframe contains a 'Pitch' column.
        has_pitch = 'Pitch' in dataframe.columns
        
        # Initialize an empty list to store the output.
        result = []
        
        # Initialize variables to keep track of the current note.
        current_velocity = None
        current_midi = None
        current_pitch = None if not has_pitch else None
        current_start = None
        current_end = None
        
        # Iterate over each row in the dataframe.
        for _, row in dataframe.iterrows():
            
            # Check if the current MIDI value is the same as the previous row
            # If so, update the current note's end time.
            if current_midi == row['MIDI'] and (not has_pitch or current_pitch == row['Pitch']):
                current_end = row['End']
            
            # If the MIDI value is different, the previous note has ended.
            # Add the previous note's details to the output list.
            else:
                if current_midi is not None:
                    if has_pitch:
                        result.append([current_velocity, current_midi, current_pitch, current_start, current_end])
                    else:
                        result.append([current_velocity, current_midi, current_start, current_end])
                
                # Update the variables to reflect the details of the new note.
                current_velocity = row['Velocity']
                current_midi = row['MIDI']
                current_pitch = row['Pitch'] if has_pitch else None
                current_start = row['Start']
                current_end = row['End']
        
        # Add the final note to the output list (if there is one).
        if current_midi is not None:
            if has_pitch:
                result.append([current_velocity, current_midi, current_pitch, current_start, current_end])
            else:
                result.append([current_velocity, current_midi, current_start, current_end])
        
        # Create a new dataframe from the output list.
        columns = ['Velocity', 'MIDI']
        if has_pitch:
            columns.append('Pitch')
        columns.extend(['Start', 'End'])
        new_dataframe = pandas.DataFrame(result, columns=columns)
        
        # Return the new dataframe as output
        return new_dataframe
    
    @staticmethod
    def convert_lists_to_scalars(dataframe):
        '''
        Convert values in a pandas dataframe that are lists or tuples of length 1 to scalars.
        
        Args:
            dataframe (pandas.DataFrame): Input dataframe.
            
        Returns:
            pandas.DataFrame: Output dataframe with values that were lists or tuples of length 1 converted to scalars.
        '''
        # Iterate over each column in the dataframe
        for col in dataframe.columns:
            # Check if the column contains objects (lists or tuples)
            if dataframe[col].dtype == object:
                # Apply a lambda function to each value in the column
                # If the value is a list or tuple of length 1, replace it with the single value
                dataframe[col] = dataframe[col].apply(lambda x: x[0] if isinstance(x, (list, tuple)) else x)
        
        return dataframe