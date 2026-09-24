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

def generate_velocity_profile(accent_binaries):
    """One velocity per accent state — ranked by rarity, spaced evenly across the range.

    The mapping is SHARED by every voice: it depends only on the accent set, never on
    which states a particular rhythm happens to reach. So a given combination of accents
    means the same velocity everywhere in the piece, and velocity is a property of the
    sieve structure rather than of the notes it lands on.

    Ordering is derived — an accent contributes its rarity (1 - density), so a sparse
    accent outranks a common one and more accents outrank fewer. Only the spacing is
    imposed, and evenly, because proportional spacing let accents of similar density earn
    near-identical weights and rendered genuinely different states 1 velocity apart.

    All 2^n states are ranked, including any this piece never reaches. Velocity is not
    volume in this project — it drives synth parameters — so there is no audibility floor
    to protect and no reason to withhold range from a state merely because the current
    rhythm misses it. Four accents give 16 levels about 8 apart across 1-127.
    """
    labels = list(accent_binaries)
    if not labels:
        return {'labels': [], 'levels': {0: UNACCENTED_VELOCITY}}

    rarity = {label: 1.0 - float(np.mean(arr)) for label, arr in accent_binaries.items()}
    states = range(1 << len(labels))
    by_rarity = sorted(states, key=lambda code: (
        sum(rarity[l] for i, l in enumerate(labels) if code >> i & 1), code))

    reach = MAX_VELOCITY - MIN_VELOCITY
    levels = {code: round(MIN_VELOCITY + reach * rank / (len(by_rarity) - 1))
              for rank, code in enumerate(by_rarity)}
    return {'labels': labels, 'levels': levels, 'rarity': rarity}

def accent_voicing(binary, accent_binaries, profile, pitch):
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
        notes_per_step[i] = [pitch]
    return notes_per_step, velocities
