"""How a step becomes a note number — the only thing that differs between modes.

Two modes, rendered side by side from one rhythm:

    static    one fixed note per voice. Pitch carries nothing, so the sieve speaks
              through rhythm and velocity alone. This is the Grandmother version, and
              the one to use when pitch is not available as a CV source.
    lattice   pitch read off the sieve's own grid. Because the base sieve's two moduli
              are coprime, every step has a unique (step mod a, step mod b) address,
              and one interval per axis turns that address into a note.

Each mode supplies `notes(cfg)` — a function from step index to MIDI note — and
`check(note_layers)`, which refuses before anything is written if its settings cannot
render correctly. Nothing here knows which sieve is in config; the lattice reads its
axes from whatever moduli the sieve uses.
"""
import math
import re

from config import *


def static_notes(cfg, note_layers):
    """One note, whatever the step."""
    note = cfg['pitch']
    return lambda step: note


def check_static(note_layers):
    """Whole-number MIDI notes, one per voice, all different."""
    for cfg in INSTRUMENT_CONFIGS:
        value = cfg['pitch']
        if type(value) is not int or not 0 <= value <= 127:
            raise ValueError(f"voice {cfg['name']}: pitch must be a whole number in "
                             f"0..127, got {value!r}")
    if len({c['pitch'] for c in INSTRUMENT_CONFIGS}) != len(INSTRUMENT_CONFIGS):
        raise ValueError("two voices share a pitch; they would be indistinguishable "
                         "in the merged file")
    return ", ".join(f"{c['name']}={c['pitch']}" for c in INSTRUMENT_CONFIGS)


def lattice_axes():
    """The lattice's two axes: the base sieve's own moduli, read from its expression.

    The grid exists because of the Chinese remainder theorem — with two COPRIME moduli
    every step has a unique address. Rows are the larger modulus, columns the smaller,
    matching PITCH_ROW_INTERVAL and PITCH_COL_INTERVAL in config.py.
    """
    moduli = sorted({int(m) for m in re.findall(r'(\d+)\s*@', INSTRUMENT_CONFIGS[0]['sieve'])},
                    reverse=True)
    if len(moduli) != 2 or math.gcd(*moduli) != 1:
        raise ValueError(f"the pitch lattice needs a base sieve in exactly two coprime "
                         f"moduli; this one uses {moduli}")
    return tuple(moduli)


def lattice_intervals():
    """One interval per axis. Derived by default: the sieve's moduli, EXCHANGED.

    The lattice is a linear map — which is what carries residue classes to residue
    classes and makes the canon an exact transposition — exactly when the row interval
    is a multiple of the column modulus and the column interval a multiple of the row
    modulus. Exchanging the two moduli is the smallest pair that qualifies, so it is the
    default, and a new sieve needs no new pitch settings. Config may still override.
    """
    row, col = lattice_axes()
    return (col if PITCH_ROW_INTERVAL is None else PITCH_ROW_INTERVAL,
            row if PITCH_COL_INTERVAL is None else PITCH_COL_INTERVAL)


def lattice_notes(cfg, note_layers):
    """Pitch read off the grid. Used to WRITE notes; check.py recomputes it another way."""
    row, col = lattice_axes()
    row_step, col_step = lattice_intervals()
    period = row * col
    return lambda step: PITCH_ROOT + (row_step * (step % row)
                                      + col_step * (step % col)) % period


def lattice_diagonal():
    """The multiplier the lattice equals: one step along both axes at once."""
    return sum(lattice_intervals())


def check_lattice(note_layers):
    """Everything the lattice claims, asserted before any file is replaced.

    Credit where due: dois_15 justified the residue-class property by BIJECTIVITY, and
    GPT showed that was wrong — most permutations of n things scatter a residue class.
    What carries classes to classes is LINEARITY, the map being multiplication by a
    unit. So that is what is checked, and the class property is then asserted directly
    rather than inferred.
    """
    row_step, col_step = lattice_intervals()
    for label, value in (('PITCH_ROOT', PITCH_ROOT),
                         ('the row interval', row_step),
                         ('the column interval', col_step)):
        if type(value) is not int:
            raise ValueError(f"{label} must be a whole number, got {value!r} "
                             f"({type(value).__name__}); MIDI notes are integers")
    row, col = lattice_axes()
    period = row * col
    off = {n: p for n, p in note_layers.items() if p != period}
    if off:
        raise ValueError(f"the {row} x {col} lattice has period {period}, but voice(s) "
                         f"{off} have other note-layer periods")
    if PITCH_ROOT < 0 or PITCH_ROOT + period - 1 > 127:
        raise ValueError(f"root {PITCH_ROOT} with {period} lattice positions reaches MIDI "
                         f"{PITCH_ROOT + period - 1}; MIDI stops at 127")

    diagonal = lattice_diagonal()
    at = lattice_notes(INSTRUMENT_CONFIGS[0], note_layers)
    for n in range(period):
        if at(n) - PITCH_ROOT != (diagonal * n) % period:
            raise ValueError(f"intervals ({row_step}, {col_step}) do "
                             f"not make the lattice linear — it disagrees with x{diagonal} "
                             f"at step {n}. Linearity needs the row interval to be a "
                             f"multiple of {col} and the column interval a multiple of {row}")
    if math.gcd(diagonal, period) != 1:
        raise ValueError(f"x{diagonal} is not invertible mod {period}: some pitches would "
                         f"be unreachable and others repeat")
    for m in (row, col):
        for r in range(m):
            landed = {(at(n) - PITCH_ROOT) % m for n in range(r, period, m)}
            if len(landed) != 1:
                raise ValueError(f"class {m}@{r} is scattered across {sorted(landed)}")
    return (f"{row} x {col} grid from the sieve's own moduli, {row_step} per "
            f"row and {col_step} per column — linear, x{diagonal} mod {period}, "
            f"a unit; MIDI {PITCH_ROOT}-{PITCH_ROOT + period - 1}")


MODES = {'static':  (static_notes,  check_static),
         'lattice': (lattice_notes, check_lattice)}
