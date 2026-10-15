"""What the sieve produces: a pattern of steps, and the voices derived from it."""
import math

import music21
import numpy as np

from transformations import (invert_binary, reverse_binary, shift_binary,
                             stretch_binary, intersect_binaries, union_binaries)


def sieve_to_binary(sieve_obj):
    return np.array(sieve_obj.segment(segmentFormat='binary'))

def evaluate(expression, span):
    """The sieve's binary over exactly `span` steps."""
    s = music21.sieve.Sieve(expression)
    s.setZRange(0, span - 1)
    binary = sieve_to_binary(s)
    if len(binary) != span:
        raise RuntimeError(f"{expression!r} gave {len(binary)} steps, expected {span}")
    return binary

def minimal_period(binary):
    """The smallest length the array actually repeats on."""
    n = len(binary)
    for p in range(1, n + 1):
        if n % p:
            continue
        if all(binary[i] == binary[i % p] for i in range(n)):
            return p
    return n

def true_period(expression):
    """The period a sieve's binary ACTUALLY repeats on."""
    nominal = music21.sieve.Sieve(expression).period()
    measured = minimal_period(evaluate(expression, nominal))
    if measured != nominal:
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
