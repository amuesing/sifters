"""How a step becomes a note number — the only thing that differs between modes."""
import math
import re

import config


def static_notes(cfg, note_layers):
    """One note, whatever the step."""
    note = cfg['pitch']
    return lambda step: note


def check_static(note_layers):
    """Whole-number MIDI notes, one per voice, all different."""
    for cfg in config.INSTRUMENT_CONFIGS:
        value = cfg['pitch']
        if type(value) is not int or not 0 <= value <= 127:
            raise ValueError(f"voice {cfg['name']}: pitch must be a whole number in "
                             f"0..127, got {value!r}")
    if len({c['pitch'] for c in config.INSTRUMENT_CONFIGS}) != len(config.INSTRUMENT_CONFIGS):
        raise ValueError("two voices share a pitch; they would be indistinguishable "
                         "in the merged file")
    return ", ".join(f"{c['name']}={c['pitch']}" for c in config.INSTRUMENT_CONFIGS)


def lattice_axes():
    """The lattice's two axes: the base sieve's own moduli, read from its expression.

    The grid exists because of the Chinese remainder theorem — with two COPRIME moduli
    every step has a unique address. Rows are the larger modulus, columns the smaller,
    matching PITCH_ROW_INTERVAL and PITCH_COL_INTERVAL in config.py.
    """
    moduli = sorted({int(m) for m in re.findall(r'(\d+)\s*@', config.INSTRUMENT_CONFIGS[0]['sieve'])},
                    reverse=True)
    if len(moduli) != 2 or math.gcd(*moduli) != 1:
        raise ValueError(f"the pitch lattice needs a base sieve in exactly two coprime "
                         f"moduli; this one uses {moduli}")
    return tuple(moduli)


def lattice_intervals():
    """One interval per axis. Derived by default: the sieve's moduli, EXCHANGED."""
    row, col = lattice_axes()
    return (col if config.PITCH_ROW_INTERVAL is None else config.PITCH_ROW_INTERVAL,
            row if config.PITCH_COL_INTERVAL is None else config.PITCH_COL_INTERVAL)


def lattice_notes(cfg, note_layers):
    """Pitch read off the grid. Used to WRITE notes; check.py recomputes it another way."""
    row, col = lattice_axes()
    row_step, col_step = lattice_intervals()
    period = row * col
    return lambda step: config.PITCH_ROOT + (row_step * (step % row)
                                      + col_step * (step % col)) % period


def lattice_diagonal():
    """The multiplier the lattice equals: one step along both axes at once."""
    return sum(lattice_intervals())


def check_lattice(note_layers):
    """Everything the lattice claims, asserted before any file is replaced."""
    row_step, col_step = lattice_intervals()
    for label, value in (('PITCH_ROOT', config.PITCH_ROOT),
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
    if config.PITCH_ROOT < 0 or config.PITCH_ROOT + period - 1 > 127:
        raise ValueError(f"root {config.PITCH_ROOT} with {period} lattice positions reaches MIDI "
                         f"{config.PITCH_ROOT + period - 1}; MIDI stops at 127")

    diagonal = lattice_diagonal()
    at = lattice_notes(config.INSTRUMENT_CONFIGS[0], note_layers)
    for n in range(period):
        if at(n) - config.PITCH_ROOT != (diagonal * n) % period:
            raise ValueError(f"intervals ({row_step}, {col_step}) do "
                             f"not make the lattice linear — it disagrees with x{diagonal} "
                             f"at step {n}. Linearity needs the row interval to be a "
                             f"multiple of {col} and the column interval a multiple of {row}")
    if math.gcd(diagonal, period) != 1:
        raise ValueError(f"x{diagonal} is not invertible mod {period}: some pitches would "
                         f"be unreachable and others repeat")
    for m in (row, col):
        for r in range(m):
            landed = {(at(n) - config.PITCH_ROOT) % m for n in range(r, period, m)}
            if len(landed) != 1:
                raise ValueError(f"class {m}@{r} is scattered across {sorted(landed)}")
    return (f"{row} x {col} grid from the sieve's own moduli, {row_step} per "
            f"row and {col_step} per column — linear, x{diagonal} mod {period}, "
            f"a unit; MIDI {config.PITCH_ROOT}-{config.PITCH_ROOT + period - 1}")


MODES = {'static':  (static_notes,  check_static),
         'lattice': (lattice_notes, check_lattice)}
