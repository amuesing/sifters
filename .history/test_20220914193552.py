import numpy as np

row = [1,2,3,4]
matrix = []


def generate_serial_matrix(row, matrix):
    interval = []
    columns = []
    matrix = []
    for tone in row:
        x = (tone - row[0])
        interval.append(x)
        columns.append([(row[0] + (row[0] - tone))] * len(row))
    print(np.add(interval, columns))
    # print(matrix)

generate_serial_matrix(row)
# print(matrix)