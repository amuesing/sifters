import numpy as np

def serial(row):
    intervals = []
    columns = []
    for tone in row:
        interval = (tone - row[0])
        intervals.append(interval)
        columns.append([(row[0] + (row[0] - tone))] * len(row))
    return np.add(intervals, columns)

def fibonacci(fund, length):
    matrix = []
    seq = []
    y = fund
    if fund == 0:
        i = 1
        for _ in range(length):
            seq.append(y)
            i, y = y, i + y
    else:
        i = fund
        for _ in range(length):
            seq.append(i)
            i, y = y, i + y
    for note in seq:
        if note == 0:
            i = 1
            for _ in range(len(seq)):
                matrix.append(note)
                note, i = i, note + i
        else:
            i = 0
            for _ in range(len(seq)):
                matrix.append(note)
                i, note = note, i + note
    return [list(array) for array in np.array_split(np.array(matrix), len(seq))]

def overtones(fund, length):
    # what if fund is 0 -- return error message
    # use enunerate for partial instead of for loop
    partial = 1
    overtones = []
    subtones = []
    matrix = []
    for _ in range(length):
        overtones.append(fund * float(partial))
        partial += 1
    partial = 1
    for _ in overtones:
        subtones.append([fund / float(partial)] * len(overtones))
        partial += 1
    for row in subtones:
        partial = 1
        for freq in row:
            matrix.append(freq * partial)
            partial += 1
    return [list(array) for array in np.array_split(np.array(matrix), len(overtones))]

#the following code takes a list such as
#[1,1,2,6,8,5,5,7,8,8,1,1,4,5,5,0,0,0,1,1,4,4,5,1,3,3,4,5,4,1,1]
#with states labeled as successive integers starting with 0
#and returns a transition matrix, M,
#where M[i][j] is the probability of transitioning from i to j

def transition_matrix(transitions):
    n = 1+ max(transitions) #number of states

    M = [[0]*n for _ in range(n)]

    for (i,j) in zip(transitions,transitions[1:]):
        M[i][j] += 1

    #now convert to probabilities:
    for row in M:
        s = sum(row)
        if s > 0:
            row[:] = [f/s for f in row]
    return M

# https://stackoverflow.com/questions/46657221/generating-markov-transition-matrix-in-python

def main(arg=None):
    t = [ 0,0,1,0,2,0,3]
    m = transition_matrix(t)
    for row in m: print(' '.join('{0:.2f}'.format(x) for x in row))

if __name__ == '__main__':
    main()