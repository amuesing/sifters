from music21 import *
from modules import *

# input = 'data/input.csv'

psappha_sieve = '((8@0|8@1|8@7)&(5@1|5@3))', '((8@0|8@1|8@2)&5@0)', '((8@5|8@6)&(5@2|5@3|5@4))', '(8@6&5@1)', '(8@3)', '(8@4)', '(8@1&5@2)'

def main():
    s = sieve_helpers.generate_score(psappha_sieve)
    s.show('text')
    # print(sieve_helpers.Largest_Prime_Factor(40))
    
if __name__ == '__main__':
    main()