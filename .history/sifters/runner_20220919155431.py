# from modules import *

# def main():
#     print(matrix_generators.fibonacci(0, 5))
    
# main()

# Split a Python List into Chunks using For Loops
a_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]

chunked_list = list()
chunk_size = 3

for i in range(0, len(a_list), chunk_size):
    chunked_list.append(a_list[i:i+chunk_size])

print(chunked_list)

# Returns: [[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11]]