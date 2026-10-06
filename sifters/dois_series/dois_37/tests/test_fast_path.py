"""The numpy shortcut in sieve.py must agree with music21 exactly, always.

dois_34 widened the residue search, which builds a new `M@a|M@b|...` expression for
every candidate it tries — hundreds of thousands of them. Parsing those with music21
was the slowest thing in the program, so unions of a single modulus now take a numpy
path. That is a shortcut around the library this project trusts for the sieve language,
so it is only safe while it is exactly equal, and these tests are what make that
checkable rather than assumed.

Anything that is NOT a plain single-modulus union must still go to music21 — the base
sieves, the intersections, the complements. That is asserted too, because a shortcut
that quietly widened its own scope would be the dangerous failure.
"""
import itertools
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import music21
import numpy as np

import sieve


class FastPathEqualsMusic21(unittest.TestCase):

    def test_every_union_of_every_modulus_up_to_40(self):
        checked = 0
        for modulus in range(1, 41):
            for size in (1, 2, 3, 5):
                if size > modulus:
                    continue
                for residues in itertools.islice(
                        itertools.combinations(range(modulus), size), 25):
                    expression = '|'.join(f'{modulus}@{r}' for r in residues)
                    for span in (40, 120, 160, modulus):
                        fast = sieve.evaluate(expression, span)
                        slow = sieve._evaluate_cached(expression, span)
                        np.testing.assert_array_equal(
                            fast, slow, f'{expression!r} over {span} steps')
                        checked += 1
        self.assertGreater(checked, 5000)

    def test_the_declared_period_matches_music21(self):
        for modulus in (1, 2, 3, 5, 7, 8, 11, 12, 16, 32, 40):
            for residues in itertools.islice(
                    itertools.combinations(range(modulus), min(3, modulus)), 20):
                expression = '|'.join(f'{modulus}@{r}' for r in residues)
                self.assertEqual(sieve.nominal_period(expression),
                                 music21.sieve.Sieve(expression).period(),
                                 expression)

    def test_anything_else_still_goes_to_music21(self):
        """The shortcut must not claim expressions it cannot evaluate."""
        import config
        others = ['(8@0|8@1)&5@0', '8@0&5@1', '5@0|8@1', '-8@0',
                  config.INSTRUMENT_CONFIGS[0]['sieve']]
        for expression in others:
            self.assertIsNone(sieve._single_modulus_binary(expression, 40), expression)

    def test_the_arrays_it_hands_out_cannot_be_written_to(self):
        """Cached arrays are shared, so a caller must not be able to corrupt them."""
        binary = sieve.evaluate('32@0|32@9', 160)
        with self.assertRaises(ValueError):
            binary[0] = 1 - binary[0]


if __name__ == '__main__':
    unittest.main()
