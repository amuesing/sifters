"""The weather, the span accent, and the velocity each note is given."""
import itertools
import math
from fractions import Fraction

import numpy as np

import config
from sieve import evaluate, sieve_moduli, true_period


# How many whole weathers derive_weather will try before it has to cut the search.
WEATHER_SEARCH_LIMIT = 500_000


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
    """The modulus M with LCM(note_layer, M) == target_span, or None.

    The smallest such M whenever the voice needs more than one pass. For a voice that
    reaches parity in ONE pass the smallest is 1 — an accent that can never switch — so
    the layer itself is used instead; see below.

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
    if modulus == 1 and note_layer > 1:
        # ONE PASS reaches parity (dois_36). The arithmetic above then gives modulus 1:
        # an accent that fires on every step, can never be off, and so carries nothing —
        # it halved the velocity profile of any single-pass voice, which could reach
        # only the weather's four states. With no repeats to tell apart, the span
        # accent's remaining job is to complete the profile.
        #
        # It takes the note layer itself as its modulus. Anything that divides the layer
        # keeps the voice ending exactly at parity after one pass, so the minimum
        # duration is untouched whichever is chosen — but a SHORT cycle is not free of
        # the weather. Measured: a 2-step accent left these voices at 7 of 8, because
        # whether a step is even is already fixed by its place in the 8-step weather
        # cycle, so some combinations can never coincide. A cycle the full length of
        # the layer can fire on any set of steps at all.
        modulus = note_layer
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


def weather_combinations(binary, firing, labels):
    """Which on/off combinations of the weather a voice's attacks actually meet."""
    return set(combination_counts(binary, firing, labels))


def combination_counts(binary, firing, labels):
    """How many of a voice's attacks, in one pass, meet each weather combination."""
    counts = {}
    for step, on in enumerate(binary):
        if on:
            combination = tuple(bool(firing[label][step]) for label in labels)
            counts[combination] = counts.get(combination, 0) + 1
    return counts


def states_reachable(binary, firing, labels, passes):
    """The most velocity states a voice can sound: one or two per weather combination.

    Two — span accent off and on — needs that combination to OCCUR at least twice in
    the voice's whole statement. Until dois_36 this was simply 2 x the combinations
    met, which silently assumed every attack recurs. It does when a voice restates its
    rhythm: the same attack comes round on every pass and the span accent can mark it
    on one pass and not another. It does not when a voice reaches parity in ONE pass —
    an attack that happens once is either on or off. Measured: with every voice on the
    same unit, B meets the both-accents combination at exactly one attack, so its real
    maximum was 7 while the old count promised 8.
    """
    return sum(min(2, count * passes)
               for count in combination_counts(binary, firing, labels).values())


def derive_weather(base_binaries, expression, note_layers, quiet=False, passes=None):
    """The shared accent field, read off the sieve instead of written by hand.

    One accent per modulus the sieve uses. For modulus m, count how many of the sieve's
    attacks land on each residue and take the half the sieve FAVOURS — its own bias in
    that modulus, made audible. Ties go to the lower residue, so the result is
    deterministic.

    Why the densest half rather than a threshold: taking residues whose count beats the
    mean gave densities anywhere from 1/5 to 2/3 across the sieves tried, and a very
    sparse or very dense accent barely distinguishes anything. Half is always half.

    THE WHOLE PROFILE, IN EVERY VOICE (new in dois_35). The densest half, taken one
    modulus at a time, is blind to what the COMBINATION does to each voice. On the
    psappha sieve it chose mod8 = 8@1|8@3|8@4|8@6, and B never has an attack where that
    accent and the mod5 one fire together — so two of the eight velocities could never
    sound in B, whatever the span accent did. The author asked for the entire velocity
    profile to be expressed, so that is now a REQUIREMENT on the weather and not a hope:
    among the densest-half candidates, keep only those where every voice's attacks meet
    every on/off combination, and of those take the one the sieve favours most. On
    psappha that is mod8 = 8@1|8@3|8@4|8@5 — one attack less dense than the blind
    choice, and mod5 is unchanged.

    If no candidate satisfies it the run is REFUSED, naming which voices fall short. The
    requirement is a property of the sieve and its voices, not something a rule can
    always deliver — but when it cannot be delivered, nothing should be written as if it
    had been.

    Each accent's period is its modulus, which divides the note layer whenever the
    sieve's period is the LCM of its moduli — that is what makes the weather STATIC,
    landing the same way on every pass. A sieve that closes earlier than its moduli
    suggest is refused here rather than silently losing that property.
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

    # Per modulus: every way of choosing the half, ranked by how much the sieve favours
    # it. The first of each list is exactly what the old blind rule returned.
    choices, counts = {}, {}
    for m in moduli:
        counts[m] = {r: int(first[r::m].sum()) for r in range(m)}
        size = max(1, m // 2)
        ranked = sorted(itertools.combinations(range(m), size),
                        key=lambda rs: (-sum(counts[m][r] for r in rs), rs))
        choices[m] = ranked

    span = max(note_layers.values())
    labels = [f'mod{m}' for m in moduli]

    def expressions(pick):
        return {f'mod{m}': "|".join(f"{m}@{r}" for r in rs) for m, rs in zip(moduli, pick)}

    passes = passes or {}
    full = 2 << len(labels)                  # every combination, span off and on

    def expresses_everything(pick):
        firing = {label: evaluate(expr, span)
                  for label, expr in expressions(pick).items()}
        return all(states_reachable(binary, firing, labels, passes.get(name, 2)) == full
                   for name, binary in base_binaries.items())

    def favour(pick):
        """How much the sieve favours a whole weather, across every modulus at once.

        Ranking each modulus on its own and taking them in order is NOT the same
        thing: it prefers keeping the first modulus at its densest over a combination
        the sieve favours equally and that serves the piece better. On psappha that
        cost a step of pass difference.
        """
        return (-sum(counts[m][r] for m, rs in zip(moduli, pick) for r in rs), pick)

    # A sieve in large moduli has too many half-sized choices to try them all (two
    # moduli of 20 already give 34 billion). Then each modulus keeps only its densest
    # few, as many as fit the budget, and the refusal below says the search was cut.
    total = math.prod(len(choices[m]) for m in moduli)
    bounded = total > WEATHER_SEARCH_LIMIT
    if bounded:
        keep = max(1, int(WEATHER_SEARCH_LIMIT ** (1 / len(moduli))))
        choices = {m: ranked[:keep] for m, ranked in choices.items()}
    for pick in sorted(itertools.product(*(choices[m] for m in moduli)), key=favour):
        if expresses_everything(pick):
            return expressions(pick)

    # REFUSE rather than fall back. Until dois_36 this printed a warning and used the
    # densest weather anyway, and nothing downstream would have caught it: the ceilings
    # are computed FROM the weather, so a voice locked out of two velocities would have
    # reported "6/6, at its ceiling" and passed — the exact failure dois_35 fixed,
    # returning behind one printed line. ChatGPT flagged it in FOR_CLAUDE.md,
    # 2026-10-05. The author has stated the full profile as a requirement, so a weather
    # that cannot deliver it is an error, not a compromise.
    densest = tuple(choices[m][0] for m in moduli)
    firing = {label: evaluate(expr, span) for label, expr in expressions(densest).items()}
    reach = {name: states_reachable(binary, firing, labels, passes.get(name, 2))
             for name, binary in base_binaries.items()}
    short = {name: f"{got}/{full}" for name, got in reach.items() if got < full}
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
    """Rank every accent state by summed rarity, then space the velocities evenly.

    EXACT fractions throughout, never floats. check.py rebuilds this table
    independently to test every rendered note against it, and it uses Fractions; if the
    renderer used floats the two could order two near-equal states differently and
    disagree about notes that are perfectly correct. That is not hypothetical — it
    happened on an 11x3 sieve, swapping velocities 73 and 91 across 95 notes.
    """
    states = range(1 << len(weights))
    by_rarity = sorted(states, key=lambda code: (
        sum((w for bit, w in enumerate(weights) if code >> bit & 1), Fraction(0)), code))
    reach = config.MAX_VELOCITY - config.MIN_VELOCITY
    return {code: round(config.MIN_VELOCITY + Fraction(reach * rank, len(by_rarity) - 1))
            for rank, code in enumerate(by_rarity)}


def shared_velocity_levels(fields):
    """ONE velocity table for the whole piece. New in dois_22."""
    labels = {name: list(bins) for name, bins in fields.items()}
    weather_orders = {tuple(l[:-1]) for l in labels.values()}
    if len(weather_orders) != 1:
        raise ValueError(f"voices order the weather differently ({weather_orders}); one "
                         f"table cannot mean the same thing in each")

    rarity_of = lambda arr: Fraction(len(arr) - int(arr.sum()), len(arr))
    weather_labels = list(weather_orders.pop())
    weights = []
    for i, label in enumerate(weather_labels):
        seen = {rarity_of(fields[name][label]) for name in fields}
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
