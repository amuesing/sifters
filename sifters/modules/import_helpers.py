import csv

def load_data(path):
    rows = []
    file = open(path)
    csvreader = csv.reader(file)
    for row in csvreader:
        rows.append(row)
    return rows

def string_to_int(input):
    matrix = []
    if any(isinstance(x, list) for x in input):
        for row in input:
            res = [eval(i) for i in row]
            matrix.append(res)
    else:
        res = [eval(i) for i in row]
        matrix.attend(res)
    return matrix

#https://stackoverflow.com/questions/952914/how-do-i-make-a-flat-list-out-of-a-list-of-lists

def flatten(l):
    return [item for sublist in l for item in sublist]