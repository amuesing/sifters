import numpy as np

# # row = [1,2,3,4]

# # def generateSerialMatrix(row):
# #     interval = []
# #     columns = []
# #     matrix = []
# #     for tone in row:
# #         interval.append(tone - row[0])
# #         columns.append(np.array(10))
# #     print(columns)
        
# # generateSerialMatrix(row)

# a = []
# b = np.array([2,3,4])
# a += b

# print(a)

#Create NumPy arrays
arr = np.array([4,7,12,12,44])
arr1 = np.array([5,9,15,44,55,66,677])

# Use concatenate() to join two arrays
con = np.concatenate((arr,arr1))
print(con)