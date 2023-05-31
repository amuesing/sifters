import math

class Composition:

    
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