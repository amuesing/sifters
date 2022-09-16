import numpy as np

row = [1,2,3,4]

def generate_serial_matrix(row):
    intervals = []
    columns = []
    for tone in row:
        interval = (tone - row[0])
        intervals.append(interval)
        columns.append([(row[0] + (row[0] - tone))] * len(row))
    return np.add(intervals, columns)


x = generate_serial_matrix(row)

print(x)