import decimal
import pandas

# Given a fundamental, find an octave above, then segment that octave by a given modulo.

# f = 110
# mod = 3
# seg = f % mod
# print(seg)

# You need to grab the specific range between the fundamental and the octave in order to maintain consistency.

# def create_subdivided_list(fundamental, divisor):
#     octave = fundamental * 2
#     rng = octave - fundamental
#     interval = rng / divisor
#     return [i*interval for i in range(divisor)]

# num = create_subdivided_list(220, 3)
# print([220 + n for n in num])
# print(num)

# fund = 220
# oct = fund * 2

# def segment_octave_by_freq(fundamental, modulo):
#     interval = fundamental / modulo
#     return [i * interval + fund for i in range(modulo)]

# list = segment_octave_by_freq(fund, 40)

# print(list)

# def segment_octave_by_period(period):
#     interval = Decimal('12') / Decimal(str(period))
#     return [float(interval * Decimal(str(i))) for i in range(period)]

# seg = segment_octave_by_period(40)

# print(seg)

# def generate_pitchclass_matrix(intervals):
#     next_interval = intervals[1:] # List of intervals, starting from the second value.
#     row = [0] + [next_interval[i] - intervals[0] for i, _ in enumerate(intervals[:-1])] # Normalize tone row.
#     matrix = [[abs(Decimal(str(note)) - 12) % 12] for note in row] # Generate matrix rows.
#     # matrix = [[abs(round(note - 12, 3)) % 12] for note in row] # Generate matrix rows.
#     matrix = [r * len(intervals) for r in matrix] # Generate matrix columns.
#     matrix = [[(matrix[i][j] + row[j]) % 12 for j, _ in enumerate(range(len(row)))] for i in range(len(row))] # Update vectors with correct value.
#     matrix = pandas.DataFrame(matrix, index=[f"P{round(m[0], 3)}" for m in matrix], columns=[f"I{round(i, 3)}" for i in matrix[0]]) # Label rows and collumns.
#     inverted_matrix = ([matrix.iloc[:, i].values.tolist() for i, _ in enumerate(matrix)])
#     return matrix

def generate_pitchclass_matrix(intervals):
    next_interval = intervals[1:] # List of intervals, starting from the second value.
    row = [0] + [next_interval[i] - intervals[0] for i, _ in enumerate(intervals[:-1])] # Normalize tone row.
    matrix = [[abs(decimal.Decimal(str(note)) - decimal.Decimal('12')) % decimal.Decimal('12')] for note in row] # Generate matrix rows.
    matrix = [r * len(intervals) for r in matrix] # Generate matrix columns.
    matrix = [[(matrix[i][j] + decimal.Decimal(str(row[j]))) % decimal.Decimal('12') for j, _ in enumerate(range(len(row)))] for i in range(len(row))] # Update vectors with correct value.
    matrix = pandas.DataFrame(matrix, index=[f'P{m[0]}' for m in matrix], columns=[f'I{i}' for i in matrix[0]]) # Label rows and collumns.
    inverted_matrix = ([matrix.iloc[:, i].values.tolist() for i, _ in enumerate(matrix)])
    return matrix


print(generate_pitchclass_matrix([0.0, 2.4, 4.8, 7.2, 9.6]))
# print(abs(9.6 - 12))5
