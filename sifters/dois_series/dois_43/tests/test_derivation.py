"""config.py pins the residues; this proves the search still derives exactly those.

From dois_42 there is one residue set per span modulus, and for every modulus whose
voices restate their layer the search is exhaustive over the sets that fill each block
halfway — 1,679,616 for psappha's 32, well under a second. `config.SPAN_RESIDUES` still
carries the answer so a render does not repeat it, and if the two ever disagree the
pinned value is stale and this fails: that is the whole point of it.
"""
import subprocess
import sys
import tempfile
import unittest

from test_dois43 import PROJECT, project_copy, run

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
weather = config.WEATHER or derive_weather(base, first['sieve'], layers, quiet=True)

def field(cfg, source, quiet=True):
    return compose.accent_field(cfg, base, layers, units, parity, weather, source, quiet)

source, used, apart, how = compose.derive_span_residues(
    field, layers, compose.state_ceilings(base, weather, layers), units, parity, base)
print(f'DERIVED {compose.format_residues(source)} apart={apart}')
print('HOW ' + ' | '.join(f'{m}: {how[m]}' for m in sorted(how, reverse=True)))
'''


class PinnedResiduesAreTheDerivedOnes(unittest.TestCase):

    def test_the_search_still_chooses_what_config_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = project_copy(tmp)
            result = subprocess.run([sys.executable, '-B', '-c', DERIVE], cwd=root,
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            line = [x for x in result.stdout.splitlines() if x.startswith('DERIVED')][0]
            self.assertEqual(line, 'DERIVED {32: (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 13, 18, 20, '
                                   '22, 27, 31), 3: (0,)} apart=8')
            how = [x for x in result.stdout.splitlines() if x.startswith('HOW')][0]
            self.assertIn('32: half of every block, the best of all 1,679,616', how)
            self.assertIn('3: half of every block, the best of all 3', how)

    def test_each_span_accent_takes_half_its_modulus(self):
        """16 of 32, and 1 of 3 — half, rounded down, as the weather takes half."""
        import sys
        sys.path.insert(0, str(PROJECT))
        try:
            import config
            for modulus, residues in config.SPAN_RESIDUES.items():
                self.assertEqual(len(residues), modulus // 2, modulus)
        finally:
            sys.path.remove(str(PROJECT))

    def test_suggest_span_reports_the_pinned_sets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = project_copy(tmp)
            result = run(root, '--suggest-span')
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('{32: (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 13, 18, 20, 22, 27, 31), 3: (0,)}',
                          result.stdout)
            self.assertIn('every pass distinct', result.stdout)


if __name__ == '__main__':
    unittest.main()
