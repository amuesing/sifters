import numpy as np

row = 

def generateSerialMatrix(row):
    interval = []
    columns = []
    matrix = []
    for tone in row:
        x = (tone - row[0])
        interval.append(x)
        columns.append([(row[0] + (row[0] - tone))] * len(row))
    print(np.add(interval, columns))
