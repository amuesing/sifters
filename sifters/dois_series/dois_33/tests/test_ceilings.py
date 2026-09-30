"""The number the whole residue search is conditioned on, checked against reality.

`state_ceilings` claims each voice can reach 2 x (the weather combinations occurring at
its attack steps) velocity states. Every version since dois_28 has searched for residues
that put every voice AT that number, so if the claim were wrong the search would be
optimising against a fiction — refusing sieves that work, or settling for less than they
can give. Nothing verified it until dois_33.

This brute-forces the same search space and compares the claim with what is actually
reachable. It must be exact in both directions: a ceiling that can be exceeded is an
under-estimate, and one that nothing reaches is an over-estimate that would make the
search refuse a workable sieve.
"""
import itertools
import math
import subprocess
import sys
import tempfile
import unittest

from test_dois33 import PROJECT, project_copy

SWEEP = '''
import itertools, math, json, sys
import config, compose
from accents import derive_weather
from sieve import build_binary

base, layers = {}, {}
for cfg in config.INSTRUMENT_CONFIGS:
    binary, period = build_binary(cfg, base)
    base[cfg['name']], layers[cfg['name']] = binary, period
units = {c['name']: compose.get_step_ticks(c) for c in config.INSTRUMENT_CONFIGS}
parity = math.lcm(*(layers[n] * units[n] for n in layers))
first = config.INSTRUMENT_CONFIGS[0]
weather = config.WEATHER or derive_weather(base[first['name']], first['sieve'], layers)
claimed = compose.state_ceilings(base, weather, layers)

def field(cfg, source, quiet=True):
    return compose.accent_field(cfg, base, layers, units, parity, weather, source, quiet)

reached = {n: 0 for n in layers}
qualifying = 0
for size in range(1, 5):
    for candidate in itertools.combinations(range(16), size):
        got = compose.try_residues(field, layers, candidate)
        if got is None:
            continue                      # this set leaves two passes identical
        qualifying += 1
        fields, levels = got
        for name, f in fields.items():
            reached[name] = max(reached[name],
                                len({int(v) for v in compose.velocities_of(f, levels) if v}))
print(json.dumps({'claimed': claimed, 'reached': reached, 'qualifying': qualifying}))
'''


class Ceilings(unittest.TestCase):

    def sweep(self, root):
        result = subprocess.run([sys.executable, '-B', '-c', SWEEP], cwd=root,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        import json
        return json.loads(result.stdout.strip().splitlines()[-1])

    def assert_exact(self, root, expected_ceilings):
        got = self.sweep(root)
        self.assertGreater(got['qualifying'], 0, 'no residue set made the passes distinct')
        self.assertEqual(got['claimed'], expected_ceilings)
        for name, claimed in got['claimed'].items():
            reached = got['reached'][name]
            self.assertLessEqual(reached, claimed,
                                 f'{name} reached {reached}, above its ceiling {claimed} '
                                 f'— state_ceilings is an UNDER-estimate')
            self.assertEqual(reached, claimed,
                             f'{name} never got past {reached} of its ceiling {claimed} '
                             f'— state_ceilings is an OVER-estimate, and the search will '
                             f'refuse sieves it should accept')

    def test_the_ceiling_is_exact_for_the_psappha_sieve(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assert_exact(project_copy(tmp), {'A': 8, 'B': 6, 'C': 8, 'D': 8})

    def test_the_ceiling_is_exact_for_a_different_sieve(self):
        """Principle VII: the claim has to hold for a sieve it was not written against."""
        with tempfile.TemporaryDirectory() as tmp:
            root = project_copy(tmp, sieve='(7@0|7@1|7@3)&(5@0|5@2|5@3)|7@5|5@1')
            self.assert_exact(root, {'A': 8, 'B': 6, 'C': 8, 'D': 6})


if __name__ == '__main__':
    unittest.main()
