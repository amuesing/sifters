"""config.py pins the residues; this proves the search still derives exactly those.

dois_34 widened the search — up to five residues below the span accent's own modulus
instead of an arbitrary four below 16 — which takes 37 seconds. Renders would pay that
every time, so `config.SPAN_RESIDUE_SOURCE` carries the answer and the derivation is run
here instead, once. If the two ever disagree, the pinned value is stale and this fails:
that is the whole point of it.
"""
import subprocess
import sys
import tempfile
import unittest

from test_dois34 import PROJECT, project_copy, run

DERIVE = '''
import math, config, compose
from accents import derive_weather, required_modulus
from sieve import build_binary

base, layers = {}, {}
for cfg in config.INSTRUMENT_CONFIGS:
    binary, period = build_binary(cfg, base)
    base[cfg['name']], layers[cfg['name']] = binary, period
units = {c['name']: compose.get_step_ticks(c) for c in config.INSTRUMENT_CONFIGS}
parity = math.lcm(*(layers[n] * units[n] for n in layers))
first = config.INSTRUMENT_CONFIGS[0]
weather = config.WEATHER or derive_weather(base[first['name']], first['sieve'], layers)

def field(cfg, source, quiet=True):
    return compose.accent_field(cfg, base, layers, units, parity, weather, source, quiet)

widest = max(required_modulus(layers[n], parity // units[n]) or 1 for n in layers)
source, used, apart = compose.derive_span_residues(
    field, layers, compose.state_ceilings(base, weather, layers), widest)
print(f'DERIVED {source} widest={widest} apart={apart}')
'''


class PinnedResiduesAreTheDerivedOnes(unittest.TestCase):

    def test_the_search_still_chooses_what_config_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = project_copy(tmp)
            result = subprocess.run([sys.executable, '-B', '-c', DERIVE], cwd=root,
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            line = [x for x in result.stdout.splitlines() if x.startswith('DERIVED')][0]
            self.assertEqual(line, 'DERIVED (0, 9, 10, 21, 31) widest=32 apart=6')

    def test_the_bound_comes_from_the_span_modulus_not_a_constant(self):
        """Principle VII: 16 was a number I chose; 32 is the sieve's own."""
        with tempfile.TemporaryDirectory() as tmp:
            root = project_copy(tmp)
            result = run(root, '--suggest-span')
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('(0, 9, 10, 21, 31)', result.stdout)
            self.assertIn('every pass distinct', result.stdout)


if __name__ == '__main__':
    unittest.main()
