import re
import numpy as np

from music21 import *

def parse_modulo(siev):
    if type(siev) == tuple:
        modulo = []
        for siv in siev:
            modulo.append([int(s) for s in re.findall(r'(\d+)@', siv)])
        return modulo
    else:
        modulo = [int(s) for s in re.findall(r'(\d+)@', siev)]
        return modulo

def find_lcm(modulo):
    if type(modulo[0]) == list:
        multiples = []
        for mod in modulo:
            multiples.append(np.lcm.reduce(mod))
        return multiples
    else:
        return np.lcm.reduce(modulo)
    
def find_repeats(period, lcm):
    repeats = []
    for m in lcm:
        repeats.append(int(period/m))
    return repeats

def merge(list1, list2):
    merged_list = [(list1[i], list2[i]) for i in range(0, len(list1))]
    return merged_list
# https://www.geeksforgeeks.org/python-merge-two-lists-into-list-of-tuples/

def normalize_periodicity(sivs):
    mod = parse_modulo(sivs)
    lcm = find_lcm(mod)
    period = find_lcm(lcm)
    repeats = find_repeats(period, lcm)
    multi = merge(sivs, repeats)
    return period

psappha_sieve = '((8@0|8@1|8@7)&(5@1|5@3))|((8@0|8@1|8@2)&5@0)|((8@5|8@6)&(5@2|5@3|5@4))|(8@3)|(8@4)|(8@1&5@2)|(8@6&5@1)'
sivs = '((8@0|8@1|8@7)&(5@1|5@3))', '((8@0|8@1|8@2)&5@0)', '((8@5|8@6)&(5@2|5@3|5@4))', '(8@6&5@1)', '(8@3)', '(8@4)', '(8@1&5@2)'
siv = '((8@0|8@1|8@7)&(5@1|5@3))'

# find LCM of each Siv

# find LCM of each LCM

# find number of repeats (multiples) 
# print(normalize_periodicity(sivs))

x = 300/8
y = 300/x

print(y)