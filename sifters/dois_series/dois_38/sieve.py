"""What the sieve produces: a pattern of steps, and the voices derived from it."""
import functools
import math
import re

import music21
import numpy as np

from transformations import (invert_binary, reverse_binary, shift_binary,
                             stretch_binary, intersect_binaries, union_binaries)


def sieve_to_binary(sieve_obj):
    return np.array(sieve_obj.segment(segmentFormat='binary'))

@functools.lru_cache(maxsize=4096)
def _evaluate_cached(expression, span):
    s = music21.sieve.Sieve(expression)
    s.setZRange(0, span - 1)
    binary = sieve_to_binary(s)
    if len(binary) != span:
        raise RuntimeError(f"{expression!r} gave {len(binary)} steps, expected {span}")
    binary.flags.writeable = False
    return binary


SINGLE_MODULUS = re.compile(r'^(\d+)@(\d+)(?:\|\1@(?:\d+))*$')


def _single_modulus_binary(expression, span):
    """`M@a|M@b|...` — one modulus, plain residues — or None if it is anything else.

    This is not an optimisation of the sieve language; it is an exact shortcut for one
    shape of it. The span accent is always this shape, and the residue search builds a
    new one for every candidate it tries, so these are the expressions music21 cannot
    cache away. `tests/test_fast_path.py` asserts the two agree on every union of every
    modulus up to 40, for every span the project uses.
    """
    if not SINGLE_MODULUS.match(expression):
        return None
    terms = expression.split('|')
    modulus = int(terms[0].split('@')[0])
    residues = {int(t.split('@')[1]) % modulus for t in terms}
    steps = np.arange(span) % modulus
    return np.isin(steps, sorted(residues)).astype(int)


@functools.lru_cache(maxsize=65536)
def _fast_cached(expression, span):
    binary = _single_modulus_binary(expression, span)
    if binary is not None:
        binary.flags.writeable = False
    return binary


def evaluate(expression, span):
    """The sieve's binary over exactly `span` steps.

    Cached: the residue search evaluates the same weather expressions thousands of
    times over, and music21 is the slowest thing in the program by a wide margin.
    The cached array is read-only so a caller cannot corrupt the next caller's copy.

    Unions of a single modulus take an exact numpy path instead of music21. Without it
    the widened search of dois_34 — up to five residues, every modulus the span accent
    uses — costs 158s per render and makes the test suite unusable.
    """
    fast = _fast_cached(expression, span)
    return fast if fast is not None else _evaluate_cached(expression, span)


def minimal_period(binary):
    """The smallest length the array actually repeats on."""
    array = np.asarray(binary)
    n = len(array)
    for p in range(1, n + 1):
        if n % p:
            continue
        if np.array_equal(array, np.tile(array[:p], n // p)):
            return p
    return n

def sieve_moduli(expression):
    """The moduli the sieve is written in, largest first — the ONE place they are read.

    Until dois_36 the accents and the pitch lattice each read them with their own
    regular expression (ChatGPT, FOR_CLAUDE.md 2026-10-05). Reading text is still how it
    is done, but the result is now checked against music21's own parse: the LCM of the
    moduli found must equal the period music21 declares for the expression. A spelling
    the pattern misread would fail that loudly instead of steering the weather and the
    lattice from wrong numbers.
    """
    found = sorted({int(m) for m in re.findall(r'(\d+)\s*@', expression)}, reverse=True)
    if not found:
        raise ValueError(f"no modulus@residue terms in {expression!r}")
    declared = nominal_period(expression)
    if math.lcm(*found) != declared:
        raise ValueError(f"read moduli {found} from {expression!r}, whose LCM is "
                         f"{math.lcm(*found)}, but music21 parses its period as "
                         f"{declared}; the expression is spelled in a way this reader "
                         f"does not understand")
    return found


def nominal_period(expression):
    """The period a sieve DECLARES, before measuring what it does.

    For a union of one modulus that IS the modulus, so the shortcut is exact and
    skips a music21 parse. That shape is what the residue search builds, hundreds of
    thousands of times, and parsing it was the single slowest thing in the program.
    """
    single = SINGLE_MODULUS.match(expression)
    return int(single.group(1)) if single else music21.sieve.Sieve(expression).period()


@functools.lru_cache(maxsize=65536)
def true_period(expression, quiet=False):
    """The period a sieve's binary ACTUALLY repeats on.

    `quiet` silences the warning for callers trying candidates in bulk — the search
    for span residues discards reducible ones by the dozen, and a warning per attempt
    would bury the render it is preparing.
    """
    nominal = nominal_period(expression)
    measured = minimal_period(evaluate(expression, nominal))
    if measured != nominal and not quiet:
        print(f"  !! {expression!r} declares modulus {nominal} but truly repeats every "
              f"{measured}. Its residues are reducible; rewrite them or the period "
              f"will be overstated.")
    return measured


RELATIONSHIPS = {
    'complement':   lambda sources, cfg: invert_binary(sources[0]),
    'retrograde':   lambda sources, cfg: reverse_binary(sources[0]),
    'shift':        lambda sources, cfg: shift_binary(sources[0], cfg['shift_amount']),
    'augmentation': lambda sources, cfg: stretch_binary(sources[0], cfg['factor']),
    'intersection': lambda sources, cfg: intersect_binaries(sources),
    'union':        lambda sources, cfg: union_binaries(sources),
}

# `augmentation` lengthens the note layer (a 40-step binary stretched by 2 states itself
# over 80), which changes that voice's period and therefore the span accent it needs.
# That is handled: layers are per-voice and span accents are derived per voice.

def tile_to(binary, span):
    """Repeat a note layer across `span`, refusing a span it does not divide."""
    if span % len(binary):
        raise ValueError(f"span {span} is not a whole number of {len(binary)}-step "
                         f"note layers")
    return np.resize(binary, span)

def voice_rhythm(cfg, base_binaries, span):
    """A voice's note layer across its full span.

    A voice defined by a sieve is EVALUATED over the span rather than tiled, so no
    assumption about its period is relied on. A derived voice applies its operation to
    its sources tiled across the same span — exact, because `tile_to` refuses a span
    the note layer does not divide.
    """
    if 'sieve' in cfg:
        return evaluate(cfg['sieve'], span)

    derives_from = cfg['derives_from']
    if isinstance(derives_from, str):
        derives_from = [derives_from]
    sources = [tile_to(base_binaries[n], span) for n in derives_from]
    return RELATIONSHIPS[cfg['relationship']](sources, cfg)

def sources_for(cfg, base_binaries):
    """The source note layers a derived voice combines, tiled to a common length.

    Sources need not share a period. Two sieves of period 40 and 35 are both defined
    over LCM(40, 35) = 280 steps, and that is where their intersection or union lives.
    Tiling each to the LCM is the only way to combine them without misaligning one.
    """
    derives_from = cfg['derives_from']
    if isinstance(derives_from, str):
        derives_from = [derives_from]
    missing = [n for n in derives_from if n not in base_binaries]
    if missing:
        raise ValueError(f"voice {cfg.get('name')!r} derives from {missing}, which "
                         f"is not defined before it")

    sources = [base_binaries[n] for n in derives_from]
    common = math.lcm(*(len(s) for s in sources))
    return [tile_to(s, common) for s in sources]

def build_binary(cfg, base_binaries):
    """One voice's note layer, at its OWN true period."""
    if 'sieve' in cfg:
        period = true_period(cfg['sieve'])
        return evaluate(cfg['sieve'], period), period

    relationship = cfg.get('relationship')
    if relationship not in RELATIONSHIPS:
        raise ValueError(f"voice {cfg.get('name')!r}: unknown relationship "
                         f"{relationship!r}. Known: {sorted(RELATIONSHIPS)}")

    result = RELATIONSHIPS[relationship](sources_for(cfg, base_binaries), cfg)
    period = minimal_period(result)
    return result[:period], period
