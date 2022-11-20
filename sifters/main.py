from modules import *

input = 'data/input.csv'

def main():
    data = import_helpers.load_data(input)
    data_stream = import_helpers.flatten(data)
    trans = matrix_generators.transition(data_stream)
    print(data)

if __name__ == '__main__':
    main()