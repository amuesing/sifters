import numpy as np

row = [1,2,3,4]

def generate_serial_matrix(row):
    interval = []
    columns = []
    matrix = []
    for tone in row:
        x = (tone - row[0])
        interval.append(x)
        columns.append([(row[0] + (row[0] - tone))] * len(row))
    y = np.add(interval, columns)
    row = y
