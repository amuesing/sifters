"""What the sieve produces: a pattern of steps, and the voices derived from it."""
import functools
import itertools
import math
import re

import music21
import numpy as np

import config

# `M@a|M@b|...`: one modulus, plain residues. Every span accent has this shape.
SINGLE_MODULUS = re.compile(r'^(\d+)@(\d+)(?:\|\1@(?:\d+))*$')


# ------------------------------------------------------------------- evaluating a sieve

@functools.lru_cache(maxsize=4096)
def _evaluate_music21(expression, span):
    s = music21.sieve.Sieve(expression)
    s.setZRange(0, span - 1)
    binary = np.array(s.segment(segmentFormat='binary'))
    if len(binary) != span:
        raise RuntimeError(f"{expression!r} gave {len(binary)} steps, expected {span}")
    binary.flags.writeable = False
    return binary


@functools.lru_cache(maxsize=65536)
def _evaluate_single_modulus(expression, span):
    """An exact shortcut for one shape of the sieve language, or None for any other.

    The residue search builds a new single-modulus expression for every candidate, and
    music21 is by far the slowest thing in the program. `tests/test_fast_path.py`
    asserts the two paths agree on every union of every modulus up to 40.
    """
    if not SINGLE_MODULUS.match(expression):
        return None
    terms = expression.split('|')
    modulus = int(terms[0].split('@')[0])
    residues = {int(t.split('@')[1]) % modulus for t in terms}
    binary = np.isin(np.arange(span) % modulus, sorted(residues)).astype(int)
    binary.flags.writeable = False
    return binary


def evaluate(expression, span):
    """The sieve's binary over exactly `span` steps: cached, and read-only so no caller
    can corrupt the next caller's copy."""
    fast = _evaluate_single_modulus(expression, span)
    return fast if fast is not None else _evaluate_music21(expression, span)


def minimal_period(binary):
    """The smallest length the array actually repeats on."""
    array = np.asarray(binary)
    n = len(array)
    for p in range(1, n + 1):
        if n % p == 0 and np.array_equal(array, np.tile(array[:p], n // p)):
            return p
    return n


def nominal_period(expression):
    """The period a sieve DECLARES (for one modulus, the modulus itself)."""
    single = SINGLE_MODULUS.match(expression)
    return int(single.group(1)) if single else music21.sieve.Sieve(expression).period()


@functools.lru_cache(maxsize=65536)
def true_period(expression, quiet=False):
    """The period a sieve's binary ACTUALLY repeats on. `quiet` silences the warning
    for callers trying candidates in bulk."""
    nominal = nominal_period(expression)
    measured = minimal_period(evaluate(expression, nominal))
    if measured != nominal and not quiet:
        print(f"  !! {expression!r} declares modulus {nominal} but truly repeats every "
              f"{measured}. Its residues are reducible; rewrite them or the period "
              f"will be overstated.")
    return measured


# ------------------------------------------------------------------ the sieve's moduli

def sieve_moduli(expression):
    """The moduli the sieve is written in, largest first. The ONE place they are read."""
    return list(_moduli(expression))


@functools.lru_cache(maxsize=1024)
def _moduli(expression):
    """Read from the text, then checked against music21's own parse: the LCM of the
    moduli found must equal the period music21 declares, so a spelling this reader
    misunderstands fails loudly instead of steering the weather and lattice wrongly."""
    found = sorted({int(m) for m in re.findall(r'(\d+)\s*@', expression)}, reverse=True)
    if not found:
        raise ValueError(f"no modulus@residue terms in {expression!r}")
    declared = nominal_period(expression)
    if math.lcm(*found) != declared:
        raise ValueError(f"read moduli {found} from {expression!r}, whose LCM is "
                         f"{math.lcm(*found)}, but music21 parses its period as "
                         f"{declared}; the expression is spelled in a way this reader "
                         f"does not understand")
    return tuple(found)


def diagonal(moduli):
    """The lattice's diagonal, d = sum(P/m) mod P, or None if there is no lattice.

    For pairwise coprime moduli with product P, every step n has a unique address
    (n mod m, ...), and the lattice that EXCHANGES the moduli is linear: it equals d*n
    mod P. For psappha d = 5 + 8 = 13: C's canon distance, the pitch lattice's
    multiplier and the wavetables' frame order. d is always a unit mod P. Moduli that
    share a factor have no lattice.
    """
    moduli = sorted(set(moduli))
    if any(math.gcd(a, b) != 1 for a, b in itertools.combinations(moduli, 2)):
        return None
    period = math.prod(moduli)
    return sum(period // m for m in moduli) % period if period > 1 else None


def ancestral_moduli(cfg, configs):
    """Every modulus written in the sieves a voice descends from."""
    by_name = {c['name']: c for c in configs}
    found, pending, seen = set(), [cfg], set()
    while pending:
        current = pending.pop()
        if current['name'] in seen:
            continue
        seen.add(current['name'])
        if 'sieve' in current:
            found.update(sieve_moduli(current['sieve']))
        else:
            pending += [by_name[n] for n in sources_of(current)]
    return sorted(found, reverse=True)


def shift_amount(cfg, configs):
    """A canon's displacement: a whole number of steps, or 'diagonal' for the
    lattice's own diagonal (13 for psappha)."""
    amount = cfg['shift_amount']
    if amount != 'diagonal':
        return amount
    found = diagonal(ancestral_moduli(cfg, configs))
    if found is None:
        raise ValueError(f"voice {cfg['name']!r} asks for the 'diagonal' shift, but the "
                         f"sieve it descends from is written in moduli "
                         f"{ancestral_moduli(cfg, configs)}, which share a factor, so it "
                         f"has no lattice diagonal. Give shift_amount as a number.")
    return found


# ------------------------------------------------- deriving one voice from another

def stretch_binary(binary, factor):
    """Augmentation: every step lasts `factor` steps, so an attack is followed by rests."""
    stretched = np.zeros(len(binary) * factor, dtype=np.asarray(binary).dtype)
    stretched[::factor] = binary
    return stretched


def _all(binaries, combine):
    result = binaries[0].copy()
    for b in binaries[1:]:
        result = combine(result, b)
    return result


RELATIONSHIPS = {
    'complement':   lambda sources, cfg: 1 - sources[0],
    'retrograde':   lambda sources, cfg: sources[0][::-1],
    'shift':        lambda sources, cfg: np.roll(
                        sources[0], shift_amount(cfg, config.INSTRUMENT_CONFIGS)),
    'augmentation': lambda sources, cfg: stretch_binary(sources[0], cfg['factor']),
    'intersection': lambda sources, cfg: _all(sources, np.bitwise_and),
    'union':        lambda sources, cfg: _all(sources, np.bitwise_or),
}


def sources_of(cfg):
    """The names a derived voice is built from."""
    derives_from = cfg['derives_from']
    return [derives_from] if isinstance(derives_from, str) else list(derives_from)


def tile_to(binary, span):
    """Repeat a note layer across `span`, refusing a span it does not divide."""
    if span % len(binary):
        raise ValueError(f"span {span} is not a whole number of {len(binary)}-step "
                         f"note layers")
    return np.resize(binary, span)


def sources_for(cfg, base_binaries):
    """A derived voice's source layers, tiled to their common length: two sieves of
    period 40 and 35 combine over LCM(40, 35) = 280 steps."""
    names = sources_of(cfg)
    missing = [n for n in names if n not in base_binaries]
    if missing:
        raise ValueError(f"voice {cfg.get('name')!r} derives from {missing}, which "
                         f"is not defined before it")
    sources = [base_binaries[n] for n in names]
    common = math.lcm(*(len(s) for s in sources))
    return [tile_to(s, common) for s in sources]


def build_binary(cfg, base_binaries):
    """One voice's note layer, at its OWN true period: (binary, period)."""
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


def voice_rhythm(cfg, base_binaries, span):
    """A voice's note layer across its full span: a sieve is evaluated over the span; a
    derived voice applies its operation to its sources tiled across it."""
    if 'sieve' in cfg:
        return evaluate(cfg['sieve'], span)
    sources = [tile_to(base_binaries[n], span) for n in sources_of(cfg)]
    return RELATIONSHIPS[cfg['relationship']](sources, cfg)
