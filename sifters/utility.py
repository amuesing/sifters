import functools
import math

class Utility:


    def get_least_common_multiple(self, nums):

        if isinstance(nums, list):
            sub_lcm = [self.get_least_common_multiple(lst) for lst in nums]

            return functools.reduce(math.lcm, sub_lcm)
        
        else:
            return nums


    def flatten_list(self, nested_list):
        
        flattened_list = []
        
        for item in nested_list:
            
            if isinstance(item, list):
                flattened_list.extend(self.flatten_list(item))
                
            else:
                flattened_list.append(item)
                
        return flattened_list
    
    
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