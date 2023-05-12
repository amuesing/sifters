import pandas
import math

class Composition:
    
    @staticmethod
    def group_by_start(dataframe):
        
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
    def group_by_start_and_end(dataframe):
        
        # Group the notes_data dataframe by the 'Start' and 'End' columns and return the unique values
        # for each column for each start and end time.
        grouped_velocity = dataframe.groupby(['Start', 'End'])['Velocity'].apply(lambda x: sorted(set(x)))
        grouped_midi = dataframe.groupby(['Start', 'End'])['MIDI'].apply(lambda x: sorted(set(x)))
        
        # If the 'Pitch' column exists in the dataframe, group it by 'Start' and 'End' and get the unique values.
        if 'Pitch' in dataframe.columns:
            grouped_pitch = dataframe.groupby(['Start', 'End'])['Pitch'].apply(lambda x: sorted(set(x)))
            # Concatenate the grouped data into a new dataframe, and re-order the columns.
            result = pandas.concat([grouped_velocity, grouped_midi, grouped_pitch], axis=1).reset_index()
            result = result[['Velocity', 'MIDI', 'Pitch', 'Start', 'End']]
        else:
            # Concatenate the grouped data into a new dataframe, and re-order the columns.
            result = pandas.concat([grouped_velocity, grouped_midi], axis=1).reset_index()
            result = result[['Velocity', 'MIDI', 'Start', 'End']]
        
        # Return the result dataframe.
        return result

    
    
    @staticmethod
    def get_lowest_midi(dataframe):
        
        dataframe['MIDI'] = dataframe['MIDI'].apply(lambda x: min(x) if x else None)
        dataframe = dataframe.dropna(subset=['MIDI'])
        if 'Pitch' in dataframe.columns:
            return dataframe[['Velocity', 'MIDI', 'Pitch', 'Start', 'End']]
        else:
            return dataframe[['Velocity', 'MIDI', 'Start', 'End']]
        
        
    def check_and_close_intervals(self, dataframe):
        
        for i in range(len(dataframe['MIDI']) - 1):
            if abs(dataframe['MIDI'][i] - dataframe['MIDI'][i + 1]) > 6: 
                dataframe = self.close_intervals(dataframe)
                return self.check_and_close_intervals(dataframe)
            
        return dataframe
    
    
    @staticmethod
    def close_intervals(dataframe):
        
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
        
        # Define the lambda function to adjust values outside the range [36, 60].
        adjust_value = lambda x: x - 12 if x > 60 else (x + 12 if x < 36 else x)
        
        # Apply the lambda function repeatedly until all values satisfy the condition.
        while dataframe['MIDI'].apply(lambda x: x < 36 or x > 60).any():
            dataframe['MIDI'] = dataframe['MIDI'].apply(adjust_value)
            
        return dataframe
    
    
    @staticmethod
    def combine_consecutive_midi_values(dataframe):
        
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
        
        # Iterate over each column in the dataframe
        for col in dataframe.columns:
            # Check if the column contains objects (lists or tuples)
            if dataframe[col].dtype == object:
                # Apply a lambda function to each value in the column
                # If the value is a list or tuple of length 1, replace it with the single value
                dataframe[col] = dataframe[col].apply(lambda x: x[0] if isinstance(x, (list, tuple)) else x)
        
        return dataframe
    
    
    @staticmethod
    def parse_pitch_data(dataframe):
        
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