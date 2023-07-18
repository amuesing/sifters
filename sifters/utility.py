import functools
import math

class Utility:

    def get_least_common_multiple(self, nums):
        if isinstance(nums, list):
            sub_lcm = [self.get_least_common_multiple(lst) for lst in nums]
            return functools.reduce(math.lcm, sub_lcm)
        else:
            return nums