"""eight_five: the same four voices with D at 8:5 instead of 4:3.

D's basic unit is a quintuplet eighth (192 ticks) instead of a triplet eighth (160), so
D runs against the others in the ratio of the sieve's own two moduli. 4800 and 7680
ticks first meet at 38,400: A, B and C state their rhythm 8 times, D 5 times, and the
piece runs 40 seconds; its form, 26'40".

Render with `python3 compose.py --piece eight_five`; files go to mid/eight_five/.
Everything not named here is config.py's.
"""
TITLE = 'eight_five'

# What the search derives for these units (64 by local search, 25 exhaustively);
# tests/test_eight_five.py fails if it ever disagrees.
SPAN_RESIDUES = {64: (0, 1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 13, 14, 17, 21, 22, 23, 25, 27, 28, 29,
                      30, 32, 34, 40, 43, 44, 47, 49, 50, 55, 60),
                 25: (0, 1, 2, 3, 4, 9, 10, 18, 21, 22)}

# Changes to config.py's voices, by name.
VOICES = {'D': {'step_ticks': 192}}     # quintuplet 8th: 8 against the sixteenth's 5
