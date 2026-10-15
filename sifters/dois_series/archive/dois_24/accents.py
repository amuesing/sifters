"""The weather, the span accent, and the velocity each note is given.

Two kinds of accent. The WEATHER is shared by every voice and its moduli come from the
sieve, so it divides the note layer and lands the same way on every pass. The SPAN
accent is derived per voice from the parity arithmetic; because its modulus does NOT
divide the note layer, it inflects each restatement differently, which is what keeps
the piece from repeating itself.

Velocity is a property of the accent STATE — which accents are sounding at that step —
not of the note. Nothing here is written by hand; see `span_accent`.
"""
import math

import numpy as np

from config import *
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


def span_accent(note_layer, target_span, residue_source=None):
    """The span accent for a voice: modulus AND residues, both derived.

    The modulus follows from the parity arithmetic (see `required_modulus`); nothing
    chooses it. The RESIDUES come from config — SPAN_RESIDUE_SOURCE, or the candidate
    passed in when compose.py is searching for a set that works — kept where they fall
    below that modulus. For this composition they are clause 1's mod-8 residues. `sieve8` is clauses 2+3, so clause 1 is exactly the clause the
    weather omits, which is also what keeps the span accent independent of `sieve8`
    rather than a refinement of it.

    At modulus 32 that gives {0,1,7}; at modulus 3, {0,1}. Both are what dois_eleven had
    written by hand.
    """
    modulus = required_modulus(note_layer, target_span)
    if modulus is None:
        raise ValueError(f"no modulus makes a {note_layer}-step layer span "
                         f"{target_span} steps; this voice cannot reach parity")
    source = SPAN_RESIDUE_SOURCE if residue_source is None else residue_source
    residues = sorted(r for r in source if r < modulus)
    if not residues:
        raise ValueError(f"modulus {modulus} is too small for any residue in {source}")
    label = f"span{modulus}"
    expression = "|".join(f"{modulus}@{r}" for r in residues)
    if true_period(expression) != modulus:
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
    """Rank every accent state by summed rarity, then space the velocities evenly.

    A sparse accent outranks a common one, and more accents outrank fewer. Only the
    SPACING is imposed: proportional spacing let accents of similar density earn
    near-identical weights and rendered genuinely different states 1 velocity apart.

    All 2^n states are ranked, including any this piece never reaches. Velocity is not
    volume here — it drives synth parameters — so there is no audibility floor to
    protect and no reason to withhold range from a state the rhythm happens to miss.
    """
    states = range(1 << len(weights))
    by_rarity = sorted(states, key=lambda code: (
        sum(w for bit, w in enumerate(weights) if code >> bit & 1), code))
    reach = MAX_VELOCITY - MIN_VELOCITY
    return {code: round(MIN_VELOCITY + reach * rank / (len(by_rarity) - 1))
            for rank, code in enumerate(by_rarity)}


def shared_velocity_levels(fields):
    """ONE velocity table for the whole piece. New in dois_22.

    Until now each voice ranked its own accents, so the same combination of accents
    could mean different velocities in different voices: with the weather alone
    sounding, A played 19 and D played 37. The weather is one field (Principle III), so
    what it MEANS should be one thing too.

    Every voice carries the same weather in the same order plus exactly one span accent,
    so bit positions already mean the same thing everywhere. Only the span accent's
    density differs between grids — span32 is rare, span3 is common — so the shared
    table weights that bit by the RAREST span in the piece. The rarest is the one whose
    presence says the most, and taking the maximum keeps the span ranked above the
    weather rather than sliding beneath it.

    `fields` maps each voice name to its accent binaries.
    """
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


def velocity_profile(accent_binaries, levels):
    """A voice's bit order paired with the piece's shared velocity table."""
    labels = list(accent_binaries)
    if not labels:
        return {'labels': [], 'levels': {0: UNACCENTED_VELOCITY}, 'rarity': {}}
    rarity = {label: 1.0 - float(np.mean(arr)) for label, arr in accent_binaries.items()}
    return {'labels': labels, 'levels': levels, 'rarity': rarity}


def accent_voicing(binary, accent_binaries, profile, note_at):
    binary = np.asarray(binary)
    n = len(binary)
    on = binary.astype(bool)

    for label, arr in accent_binaries.items():
        if len(arr) != n:
            raise RuntimeError(f"accent {label!r} has {len(arr)} steps, voice has {n}")

    # Which accents are present picks the level — not merely how many of them.
    code = accent_code(accent_binaries, profile['labels'], n)
    velocities = np.zeros(n, dtype=int)
    velocities[on] = [profile['levels'][c] for c in code[on]]

    notes_per_step = [[] for _ in range(n)]
    for i in np.flatnonzero(on):
        notes_per_step[i] = [note_at(int(i))]
    return notes_per_step, velocities
