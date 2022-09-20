# from modules import *

# def main():
#     print(matrix_generators.fibonacci(0, 5))
    
# main()



import numpy as np

a_list = [1, 2, 3, 4, 5, 6, 7, 8, 9]
our_array = np.array(a_list)

chunked_arrays = np.array_split(our_array, 3)
chunked_list = [list(array) for array in np.array_split(np.array(our_list), 3)]

print(chunked_list)

# Returns: [[1, 2, 3], [4, 5, 6], [7, 8, 9]]