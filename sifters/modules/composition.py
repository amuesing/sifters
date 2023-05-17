import pandas
import math

class Composition:
    
    @staticmethod
    def group_by_start(dataframe):
        # Sort the DataFrame by the "Start" column
        dataframe = dataframe.sort_values('Start')

        # Group the sorted DataFrame by the "Start" column and create a new DataFrame with lists of values
        dataframe = dataframe.groupby('Start').agg({'Velocity': list, 'MIDI': list, 'Duration': list}).reset_index()
        
        return dataframe

    
    @staticmethod
    def get_closest_midi(dataframe):
        
        # Iterate over the dataframe rows
        for i in range(len(dataframe)):
            current_row = dataframe.loc[i]

            if len(current_row['MIDI']) > 1:
                min_midi_index = current_row['MIDI'].index(min(current_row['MIDI']))
                selected_midi_value = current_row['MIDI'][min_midi_index]
                dataframe.loc[i, 'MIDI'] = [selected_midi_value]
                dataframe.loc[i, 'Velocity'] = [current_row['Velocity'][min_midi_index]]
                dataframe.loc[i, 'Duration'] = [current_row['Duration'][min_midi_index]]

            if i < len(dataframe) - 1:
                next_row = dataframe.loc[i + 1]

                if len(current_row['MIDI']) == 1 and len(next_row['MIDI']) > 1:
                    current_midi = current_row['MIDI'][0]
                    next_midi_values = next_row['MIDI']
                    closest_midi = min(next_midi_values, key=lambda x: abs(x - current_midi))
                    dataframe.loc[i + 1, 'MIDI'] = [closest_midi]
                    dataframe.loc[i + 1, 'Velocity'] = next_row['Velocity'][next_midi_values.index(closest_midi)]
                    dataframe.loc[i + 1, 'Duration'] = next_row['Duration'][next_midi_values.index(closest_midi)]

        # Print the updated dataframe
        return dataframe
        
    # If I run check_and_close_intervals I will get values that are too low or too high. (negative numbers)
    def check_and_close_intervals(self, dataframe):
        
        for i in range(len(dataframe['MIDI']) - 1):
            if abs(dataframe['MIDI'][i] - dataframe['MIDI'][i + 1]) > 6: 
                dataframe = self.close_intervals(dataframe)
                return self.check_and_close_intervals(dataframe)
            
        return dataframe
    
    
    @staticmethod
    def close_intervals(dataframe):
        
        # Make a copy of the input dataframe.
        updated_dataframe = dataframe.copy()
        
        # Iterate through each pair of consecutive MIDI values.
        for i, midi in enumerate(updated_dataframe["MIDI"][:-1]):
            next_midi = updated_dataframe["MIDI"][i + 1]
            
            # If the increase between midi notes is greater than a tritone, transpose
            # the next midi note up one octave.
            if midi - next_midi > 6:
                updated_dataframe.at[i + 1, "MIDI"] = round(next_midi + 12, 3)
            
            # If the decrease between midi notes is greater than a tritone, transpose
            # the next midi note down one octave.
            elif midi - next_midi < -6:
                updated_dataframe.at[i + 1, "MIDI"] = round(next_midi - 12, 3)
        
        # Return the updated dataframe.
        return updated_dataframe
    
    
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
    
        i = 0
        while i < len(dataframe) - 1:
            if dataframe.loc[i, 'MIDI'] == dataframe.loc[i + 1, 'MIDI']:
                if (dataframe.loc[i, 'Start'] + dataframe.loc[i, 'Duration']) < dataframe.loc[i + 1, 'Start']:
                    i += 1
                else:
                    dataframe.loc[i, 'Duration'] += dataframe.loc[i + 1, 'Duration']
                    dataframe = dataframe.drop(i + 1).reset_index(drop=True)
            else:
                i += 1

        return dataframe
    # # update this so that the durational values are combined when combining dataframe rows
    # @staticmethod
    # def combine_consecutive_midi_values(dataframe):
        
    #     # Check if the dataframe contains a 'Pitch' column.
    #     has_pitch = 'Pitch' in dataframe.columns
        
    #     # Initialize an empty list to store the output.
    #     result = []
        
    #     # Initialize variables to keep track of the current note.
    #     current_velocity = None
    #     current_midi = None
    #     current_pitch = None if not has_pitch else None
    #     current_start = None
    #     current_duration = None
        
    #     # Iterate over each row in the dataframe.
    #     for _, row in dataframe.iterrows():
            
    #         # Check if the current MIDI value is the same as the previous row
    #         # If so, update the current note's end time.
    #         if current_midi == row['MIDI'] and (not has_pitch or current_pitch == row['Pitch']):
    #             current_duration = row['Duration']
            
    #         # If the MIDI value is different, the previous note has ended.
    #         # Add the previous note's details to the output list.
    #         else:
    #             if current_midi is not None:
    #                 if has_pitch:
    #                     result.append([current_velocity, current_midi, current_pitch, current_start, current_duration])
    #                 else:
    #                     result.append([current_velocity, current_midi, current_start, current_duration])
                
    #             # Update the variables to reflect the details of the new note.
    #             current_velocity = row['Velocity']
    #             current_midi = row['MIDI']
    #             current_pitch = row['Pitch'] if has_pitch else None
    #             current_start = row['Start']
    #             current_duration = row['Duration']
        
    #     # Add the final note to the output list (if there is one).
    #     if current_midi is not None:
    #         if has_pitch:
    #             result.append([current_velocity, current_midi, current_pitch, current_start, current_duration])
    #         else:
    #             result.append([current_velocity, current_midi, current_start, current_duration])
        
    #     # Create a new dataframe from the output list.
    #     columns = ['Velocity', 'MIDI']
    #     if has_pitch:
    #         columns.append('Pitch')
    #     columns.extend(['Start', 'Duration'])
    #     new_dataframe = pandas.DataFrame(result, columns=columns)
        
    #     # Return the new dataframe as output
    #     return new_dataframe
    
    
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
        column_order = ['Velocity', 'MIDI', 'Pitch', 'Start', 'Duration']
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