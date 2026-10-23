"""The weather, the span accent, and the velocity each note is given."""
import itertools
import math
from fractions import Fraction

import numpy as np

import config
from sieve import evaluate, sieve_moduli, true_period

WEATHER_SEARCH_LIMIT = 500_000      # whole weathers derive_weather tries before cutting


def prime_factors(n):
    factors, d = {}, 2
    while d * d <= n:
        while n % d == 0:
            factors[d] = factors.get(d, 0) + 1
            n //= d
        d += 1
    if n > 1:
        factors[n] = factors.get(n, 0) + 1
    return factors


def required_modulus(note_layer, target_span):
    """The span accent's modulus M, with LCM(note_layer, M) == target_span, or None.

    The accent must make the voice state itself exactly `target_span` steps, which fixes
    M: for each prime, whatever exponent the target needs beyond the layer's. When ONE
    pass reaches parity that gives M = 1, an accent that can never switch off, so the
    layer itself is used: a full-length cycle can fire on any set of steps, where a
    short one is tied to the weather's own cycle (a 2-step accent left voices at 7 of 8
    states).
    """
    layer_f, target_f = prime_factors(note_layer), prime_factors(target_span)
    if any(layer_f.get(prime, 0) > power for prime, power in target_f.items()):
        return None                       # the layer already over-shoots the target
    if any(prime not in target_f for prime in layer_f):
        return None                       # the layer has a prime the target lacks
    modulus = 1
    for prime, power in target_f.items():
        if layer_f.get(prime, 0) < power:
            modulus *= prime ** power
    if modulus == 1 and note_layer > 1:
        modulus = note_layer
    return modulus if math.lcm(note_layer, modulus) == target_span else None


def duplicate_passes(velocities, note_layer):
    """Which pairs of a voice's passes came out identical (Principle IV): empty when
    every restatement differs."""
    count = len(velocities) // note_layer
    passes = [tuple(velocities[i * note_layer:(i + 1) * note_layer]) for i in range(count)]
    return [(i + 1, j + 1) for i in range(count) for j in range(i + 1, count)
            if passes[i] == passes[j]]


def combination_counts(binary, firing, labels):
    """How many of a voice's attacks, in one pass, meet each weather combination."""
    counts = {}
    for step, on in enumerate(binary):
        if on:
            combination = tuple(bool(firing[label][step]) for label in labels)
            counts[combination] = counts.get(combination, 0) + 1
    return counts


def states_reachable(binary, firing, labels, passes):
    """The most velocity states a voice can sound: per weather combination, two (span
    accent off and on) if it occurs at least twice in the whole statement, else one."""
    return sum(min(2, count * passes)
               for count in combination_counts(binary, firing, labels).values())


def derive_weather(base_binaries, expression, note_layers, quiet=False, passes=None):
    """The shared accent field, read off the sieve: one accent per modulus it uses.

    For modulus m, the half of the residues the sieve's attacks FAVOUR (densest first,
    ties to the lower residue): the sieve's own bias, made audible. Among those choices
    only weathers under which every voice meets every on/off combination qualify, so the
    whole velocity profile can sound in every voice; of those, the one the sieve favours
    most across all moduli at once. If none qualifies the run is refused.

    Each accent's period is its modulus, which divides the note layer, so the weather
    is STATIC: it lands the same way on every pass.
    """
    moduli = sieve_moduli(expression)
    first = next(iter(base_binaries.values()))
    for m in moduli:
        for name, period in note_layers.items():
            if period % m:
                raise ValueError(
                    f"the sieve is written in modulus {m} but voice {name} closes on "
                    f"{period} steps, which {m} does not divide, so an accent on {m} "
                    f"would not be static. Give WEATHER explicitly for this sieve.")

    choices, counts = {}, {}
    for m in moduli:
        counts[m] = {r: int(first[r::m].sum()) for r in range(m)}
        choices[m] = sorted(itertools.combinations(range(m), max(1, m // 2)),
                            key=lambda rs: (-sum(counts[m][r] for r in rs), rs))

    span = max(note_layers.values())
    labels = [f'mod{m}' for m in moduli]
    passes = passes or {}
    full = 2 << len(labels)                  # every combination, span off and on

    def expressions(pick):
        return {f'mod{m}': "|".join(f"{m}@{r}" for r in rs) for m, rs in zip(moduli, pick)}

    def reach(pick):
        firing = {label: evaluate(expr, span) for label, expr in expressions(pick).items()}
        return {name: states_reachable(binary, firing, labels, passes.get(name, 2))
                for name, binary in base_binaries.items()}

    def favour(pick):
        return (-sum(counts[m][r] for m, rs in zip(moduli, pick) for r in rs), pick)

    # Large moduli have too many half-sized choices to try (two moduli of 20 give 34
    # billion); then each keeps only its densest few, and a refusal says so.
    total = math.prod(len(choices[m]) for m in moduli)
    bounded = total > WEATHER_SEARCH_LIMIT
    if bounded:
        keep = max(1, int(WEATHER_SEARCH_LIMIT ** (1 / len(moduli))))
        choices = {m: ranked[:keep] for m, ranked in choices.items()}
    for pick in sorted(itertools.product(*(choices[m] for m in moduli)), key=favour):
        if all(got == full for got in reach(pick).values()):
            return expressions(pick)

    densest = tuple(choices[m][0] for m in moduli)
    short = {name: f"{got}/{full}" for name, got in reach(densest).items() if got < full}
    searched = (f"the densest {keep} half-sized choice(s) per modulus — the full set "
                f"is {total:,}, too many to try, so this is NOT a proof" if bounded
                else f"every half-sized choice per modulus, {total:,} in all")
    raise ValueError(
        f"no weather lets every voice's attacks meet every on/off combination of the "
        f"accents, so the whole velocity profile cannot sound in every voice. Searched "
        f"{searched}. Under the densest weather these voices can reach only: "
        f"{short}. Name a WEATHER in config.py that does, or change the sieve or the "
        f"voices. Nothing was written.")


def span_accent(note_layer, target_span, residue_source=None, quiet=False):
    """The span accent for a voice, (label, expression): modulus and residues, derived.

    Residues come one set per modulus, `{modulus: residues}`. A plain sequence is read
    as one shared set, kept below each modulus, for tests and studies that sweep it.
    """
    modulus = required_modulus(note_layer, target_span)
    if modulus is None:
        raise ValueError(f"no modulus makes a {note_layer}-step layer span "
                         f"{target_span} steps; this voice cannot reach parity")
    source = config.SPAN_RESIDUES if residue_source is None else residue_source
    if source is None:
        raise ValueError("no span residues given and none derived yet")
    if isinstance(source, dict):
        if modulus not in source:
            raise ValueError(f"SPAN_RESIDUES has no set for modulus {modulus}; it names "
                             f"{sorted(source)}. They were pinned for another sieve or other "
                             f"basic units — set SPAN_RESIDUES = None in config.py and the "
                             f"search derives this one's. Nothing was written.")
        residues = sorted(source[modulus])
        if any(not 0 <= r < modulus for r in residues):
            raise ValueError(f"SPAN_RESIDUES[{modulus}] = {tuple(residues)} has residues "
                             f"outside 0..{modulus - 1}")
    else:
        residues = sorted(r for r in source if r < modulus)
    if not residues:
        raise ValueError(f"modulus {modulus} is too small for any residue in {source}")
    expression = "|".join(f"{modulus}@{r}" for r in residues)
    if true_period(expression, quiet) != modulus:
        raise ValueError(f"{expression!r} reduces below modulus {modulus}; its residues "
                         f"are not irreducible and the span would be wrong")
    return f"span{modulus}", expression


def voice_span(rhythm_period, accent_dict):
    """Steps in one full statement: the LCM of the rhythm and the accents' TRUE periods.
    An accent that does not divide the rhythm lands differently on each pass."""
    return math.lcm(rhythm_period, *(true_period(p) for p in accent_dict.values()))


def create_accent_binaries(accent_dict, span):
    """Accent masks across the voice's FULL span, so no accent restarts with each pass."""
    return {label: evaluate(pattern, span) for label, pattern in accent_dict.items()}


def levels_from_weights(weights):
    """Every accent state ranked by summed rarity, velocities spaced evenly across it.

    Exact fractions, never floats: check.py rebuilds this table independently, and
    floats once ordered two near-equal states differently on an 11x3 sieve.
    """
    states = range(1 << len(weights))
    by_rarity = sorted(states, key=lambda code: (
        sum((w for bit, w in enumerate(weights) if code >> bit & 1), Fraction(0)), code))
    reach = config.MAX_VELOCITY - config.MIN_VELOCITY
    return {code: round(config.MIN_VELOCITY + Fraction(reach * rank, len(by_rarity) - 1))
            for rank, code in enumerate(by_rarity)}


def shared_velocity_levels(fields):
    """ONE velocity table for the whole piece, so a state means one velocity everywhere."""
    labels = {name: list(bins) for name, bins in fields.items()}
    weather_orders = {tuple(l[:-1]) for l in labels.values()}
    if len(weather_orders) != 1:
        raise ValueError(f"voices order the weather differently ({weather_orders}); one "
                         f"table cannot mean the same thing in each")

    def rarity(arr):
        return Fraction(len(arr) - int(arr.sum()), len(arr))

    weights = []
    for label in weather_orders.pop():
        seen = {rarity(fields[name][label]) for name in fields}
        if len(seen) != 1:
            raise ValueError(f"weather accent {label!r} has different densities per voice "
                             f"({seen}); it is not static and cannot be shared")
        weights.append(seen.pop())
    weights.append(max(rarity(bins[labels[name][-1]]) for name, bins in fields.items()))
    return levels_from_weights(weights)


def step_velocities(binary, accent_binaries, levels):
    """A velocity for every sounding step, zero where the voice is silent. It depends on
    which accents fire (the STATE) and never on pitch."""
    binary = np.asarray(binary)
    n = len(binary)
    for label, arr in accent_binaries.items():
        if len(arr) != n:
            raise RuntimeError(f"accent {label!r} has {len(arr)} steps, voice has {n}")
    code = np.zeros(n, dtype=int)
    for bit, arr in enumerate(accent_binaries.values()):
        code += (1 << bit) * arr.astype(int)
    on = binary.astype(bool)
    velocities = np.zeros(n, dtype=int)
    velocities[on] = [levels[c] for c in code[on]]
    return velocities


def velocities_of(field, levels):
    """A voice's velocities, given its accent field and the piece's shared table."""
    return step_velocities(field['rhythm'], field['accents'], levels)


def notes_for_steps(velocities, note_at):
    """Which note sounds at each step. Velocities are never below 1, so a non-zero
    velocity is exactly a sounding step."""
    return [[note_at(step)] if velocity else [] for step, velocity in enumerate(velocities)]
