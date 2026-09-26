"""The weather, the span accent, and the velocity each note is given."""
import math
import re

import numpy as np

import config
from sieve import evaluate, true_period


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
    """The smallest modulus M with LCM(note_layer, M) == target_span, or None.

    The span accent's job is to make a voice state itself exactly `target_span` steps —
    long enough to inflect every restatement parity forces, and no longer. That fixes
    its modulus completely: for each prime, the accent must supply whatever exponent the
    target needs beyond what the note layer already has.
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
    return modulus if math.lcm(note_layer, modulus) == target_span else None

def duplicate_passes(velocities, note_layer):
    """Which passes of the note layer came out identical.

    Reaching parity forces a voice to restate its rhythm; the span accent is what makes
    each restatement different. If two passes match, that repetition is bare and
    Principle IV is broken. Returns the offending pairs, empty when all differ.
    """
    count = len(velocities) // note_layer
    passes = [tuple(velocities[i * note_layer:(i + 1) * note_layer]) for i in range(count)]
    return [(i + 1, j + 1) for i in range(count) for j in range(i + 1, count)
            if passes[i] == passes[j]]


def sieve_moduli(expression):
    """The moduli the sieve is written in, largest first."""
    found = sorted({int(m) for m in re.findall(r'(\d+)\s*@', expression)}, reverse=True)
    if not found:
        raise ValueError(f"no modulus@residue terms in {expression!r}")
    return found


def derive_weather(base_binary, expression, note_layers):
    """The shared accent field, read off the sieve instead of written by hand.

    One accent per modulus the sieve uses. For modulus m, count how many of the sieve's
    attacks land on each residue and take the half the sieve FAVOURS — its own bias in
    that modulus, made audible. Ties go to the lower residue, so the result is
    deterministic.

    Why the densest half rather than a threshold: taking residues whose count beats the
    mean gave densities anywhere from 1/5 to 2/3 across the sieves tried, and a very
    sparse or very dense accent barely distinguishes anything. Half is always half.

    Each accent's period is its modulus, which divides the note layer whenever the
    sieve's period is the LCM of its moduli — that is what makes the weather STATIC,
    landing the same way on every pass. A sieve that closes earlier than its moduli
    suggest is refused here rather than silently losing that property.
    """
    weather = {}
    for m in sieve_moduli(expression):
        for name, period in note_layers.items():
            if period % m:
                raise ValueError(
                    f"the sieve is written in modulus {m} but voice {name} closes on "
                    f"{period} steps, which {m} does not divide, so an accent on {m} "
                    f"would not be static. Give WEATHER explicitly for this sieve.")
        counts = {r: int(base_binary[r::m].sum()) for r in range(m)}
        favoured = sorted(sorted(counts, key=lambda r: (-counts[r], r))[:max(1, m // 2)])
        weather[f'mod{m}'] = "|".join(f"{m}@{r}" for r in favoured)
    return weather


def span_accent(note_layer, target_span, residue_source=None, quiet=False):
    """The span accent for a voice: modulus AND residues, both derived."""
    modulus = required_modulus(note_layer, target_span)
    if modulus is None:
        raise ValueError(f"no modulus makes a {note_layer}-step layer span "
                         f"{target_span} steps; this voice cannot reach parity")
    source = config.SPAN_RESIDUE_SOURCE if residue_source is None else residue_source
    residues = sorted(r for r in source if r < modulus)
    if not residues:
        raise ValueError(f"modulus {modulus} is too small for any residue in {source}")
    label = f"span{modulus}"
    expression = "|".join(f"{modulus}@{r}" for r in residues)
    if true_period(expression, quiet) != modulus:
        raise ValueError(f"{expression!r} reduces below modulus {modulus}; its residues "
                         f"are not irreducible and the span would be wrong")
    return label, expression

def voice_span(rhythm_period, accent_dict):
    """Steps in one full statement: LCM of the rhythm and the TRUE accent periods.

    The note layer repeats every `rhythm_period` steps, but an accent whose modulus
    does not divide that lands differently on each pass, so the voice has not stated
    itself until the two realign. Uses measured periods, not nominal ones.
    """
    periods = [rhythm_period] + [true_period(p) for p in accent_dict.values()]
    return math.lcm(*periods)

def create_accent_binaries(accent_dict, span):
    """Accent masks across the voice's FULL span, not one rhythm period.

    Evaluating them over the rhythm period alone would restart every accent at each
    repeat, which is what flattens the re-accenting away.
    """
    return {label: evaluate(pattern, span) for label, pattern in accent_dict.items()}

def accent_code(accent_binaries, labels, n):
    """One integer per step: a bitmask of which accents are firing there."""
    code = np.zeros(n, dtype=int)
    for i, label in enumerate(labels):
        code += (1 << i) * accent_binaries[label].astype(int)
    return code

def levels_from_weights(weights):
    """Rank every accent state by summed rarity, then space the velocities evenly."""
    states = range(1 << len(weights))
    by_rarity = sorted(states, key=lambda code: (
        sum(w for bit, w in enumerate(weights) if code >> bit & 1), code))
    reach = config.MAX_VELOCITY - config.MIN_VELOCITY
    return {code: round(config.MIN_VELOCITY + reach * rank / (len(by_rarity) - 1))
            for rank, code in enumerate(by_rarity)}


def shared_velocity_levels(fields):
    """ONE velocity table for the whole piece. New in dois_22."""
    labels = {name: list(bins) for name, bins in fields.items()}
    weather_orders = {tuple(l[:-1]) for l in labels.values()}
    if len(weather_orders) != 1:
        raise ValueError(f"voices order the weather differently ({weather_orders}); one "
                         f"table cannot mean the same thing in each")

    rarity_of = lambda arr: 1.0 - float(np.mean(arr))
    weather_labels = list(weather_orders.pop())
    weights = []
    for i, label in enumerate(weather_labels):
        seen = {round(rarity_of(fields[name][label]), 12) for name in fields}
        if len(seen) != 1:
            raise ValueError(f"weather accent {label!r} has different densities per voice "
                             f"({seen}); it is not static and cannot be shared")
        weights.append(seen.pop())
    weights.append(max(rarity_of(bins[labels[name][-1]]) for name, bins in fields.items()))
    return levels_from_weights(weights)


def step_velocities(binary, accent_binaries, levels):
    """A velocity for every sounding step, zero where the voice is silent.

    Velocity depends on the accent STATE alone and never on pitch. That is why it is
    computed once per voice and shared by every pitch mode: the modes are one piece
    heard different ways, not different pieces.
    """
    binary = np.asarray(binary)
    n = len(binary)
    on = binary.astype(bool)
    for label, arr in accent_binaries.items():
        if len(arr) != n:
            raise RuntimeError(f"accent {label!r} has {len(arr)} steps, voice has {n}")

    # Which accents are present picks the level — not merely how many of them.
    code = accent_code(accent_binaries, list(accent_binaries), n)
    velocities = np.zeros(n, dtype=int)
    velocities[on] = [levels[c] for c in code[on]]
    return velocities


def notes_for_steps(velocities, note_at):
    """Which note sounds at each step — the one thing a pitch mode decides.

    A sounding step always has a velocity of at least MIN_VELOCITY, which is 1 or more
    (MIDI reads a note-on of velocity 0 as a note-off), so a non-zero velocity is
    exactly a sounding step. check.py asserts that floor on every rendered note.
    """
    return [[note_at(step)] if velocity else [] for step, velocity in enumerate(velocities)]
