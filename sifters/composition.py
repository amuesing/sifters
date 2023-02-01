
'''
The following code represents an attempt to generate and aggregate
grid changes based on the multipliers (number of repititions) so that
parts would be of equal length, but on each repition there will be a 
change of the grid ratio.
'''

def distribute_grid(*args, multipliers):
    normalized_grid = []
    for arg, multiplier in zip(args, multipliers):
        total = arg.grid.numerator * multiplier
        lcd = find_least_common_denominator(arg)
        total = normalize_denominator(arg, lcd, multiplier)
        numbers = multiple_range(arg.grid.denominator, total)
        combo = find_combinations(numbers, total, multiplier)
        print(combo)
        # min_range_tuple = find_min_range_tuple(combinations)
    #     normalized_grid.append((distribute_numerator(arg, min_range_tuple)))
    # return normalized_grid
    
def find_least_common_denominator(arg):
    lcd = 1
    for frac in arg.grid_history:
        lcd = math.lcm(lcd, frac.denominator)
    return lcd

def multiple_range(number, target):
    result = []
    multiple = number
    while multiple <= target:
        result.append(multiple)
        multiple += number
    return result

    
def normalize_denominator(arg, lcd, mult):
    m = lcd // arg.grid.denominator
    return (arg.grid.numerator * m) * mult

def find_combinations(numbers, total, length):
    # Find all combinations of the given length within the set of numbers
    combinations = [c for c in itertools.combinations(numbers, length)]
    # Filter the combinations that add up to the given total and that don't contain 0
    return [c for c in combinations if sum(c) == total and 0 not in c]

def find_min_range_tuple(tuples):
    min_range = float("inf")
    min_tuple = None
    for tup in tuples:
        range = max(tup) - min(tup)
        if range < min_range:
            min_range = range
            min_tuple = tup
    return min_tuple

def distribute_numerator(arg, tuple):
    normalized_fractions = []
    for num in tuple:
        normalized_fractions.append(fractions.Fraction(num, arg.grid.denominator))
    return normalized_fractions

def create_distributed_segment(distributed_grid):
    parts = []
    for part in distributed_grid:
        segment = []
        for grid in part:
            perc = Percussion(sivs=sivs, grid=grid)
            segment.append(perc)
        parts.append(segment)
    return parts

def combine_segments(parts):
    offset_history = []
    for part in parts:
        offset = []
        for i, segment in enumerate(part):
            length_of_one_rep = math.pow(segment.period, 2)
            # print(segment.dataframe['Offset'] + (length_of_one_rep * segment.grid) * i)
            offset.append((length_of_one_rep * segment.grid) * i)
        offset_history.append(offset)
    return offset_history
                
# distributed = distribute_grid(perc1, perc2, perc3, multipliers=score.multipliers)
# parts = create_distributed_segment(distributed)
# df = parts[0][3].dataframe
# print(combine_segments(parts))