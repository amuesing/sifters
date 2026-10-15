"""How a step becomes a note number: the only thing that differs between pitch modes."""
import math

import config
from sieve import shift_amount, sieve_moduli, sources_of


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
    """The lattice's axes: the base sieve's two COPRIME moduli, larger first, so that
    every step has a unique address (the Chinese remainder theorem)."""
    moduli = sieve_moduli(config.INSTRUMENT_CONFIGS[0]['sieve'])
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
    """Pitch read off the grid. check.py recomputes it another way, as a multiplier."""
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


def source_step(cfg, step, note_layers):
    """The step of the base sieve a voice's note at `step` descends from.

    A shift reads back by its distance, a retrograde reflects, an augmentation divides.
    A complement, intersection or union keeps the step (following its FIRST source).
    """
    by_name = {c['name']: c for c in config.INSTRUMENT_CONFIGS}
    current, at = cfg, step
    while 'sieve' not in current:
        source = by_name[sources_of(current)[0]]
        relationship = current['relationship']
        if relationship == 'shift':
            at -= shift_amount(current, config.INSTRUMENT_CONFIGS)
        elif relationship == 'retrograde':
            at = note_layers[source['name']] - 1 - at
        elif relationship == 'augmentation':
            at //= current['factor']
        current = source
    return at


def canon_notes(cfg, note_layers):
    """The lattice, read at the step each note descends from: C, A's canon 13 steps
    later, plays A's melody 13 steps later, and where they meet they sound a fixed
    interval (31 lattice steps, 930 cents in the 40-step tuning) instead of a unison."""
    at = lattice_notes(cfg, note_layers)
    return lambda step: at(source_step(cfg, step, note_layers))


def check_canon(note_layers):
    """The lattice's own requirements, plus where each voice reads it from."""
    described = check_lattice(note_layers)
    reads = []
    for cfg in config.INSTRUMENT_CONFIGS:
        offset = source_step(cfg, 0, note_layers)
        reads.append(f"{cfg['name']} at its own step" if offset == 0
                     else f"{cfg['name']} at step n {offset:+d}")
    return described + "; read at each note's source step: " + ", ".join(reads)


MODES = {'static':  (static_notes,  check_static),
         'lattice': (lattice_notes, check_lattice),
         'canon':   (canon_notes,   check_canon)}
