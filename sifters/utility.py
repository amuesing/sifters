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