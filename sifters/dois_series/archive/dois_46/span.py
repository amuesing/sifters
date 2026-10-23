"""The span accents' residues: one set per span modulus, derived from what the passes need.

The span accent is the one accent that moves: the weather marks every pass of a voice the
same way, so the span accent alone tells the passes apart (Principle IV). Parity forces
its modulus; its residues are chosen here.

WHY THE SEARCH IS EXACT. Pass k of a voice reads the accent at (k * L + i) mod M for
layer step i (L the layer, M the modulus). Those positions form one block, the residues
congruent to i mod gcd(L, M), with exactly as many positions as there are passes. So a
residue set is a choice of which positions to fill in each block, independently.

HALF FULL. An attack whose block holds f filled positions of n differs between f(n - f)
pass pairs, most when f = n/2. Making the passes differ as much as possible in total
therefore fills every block halfway: the accent takes half its modulus, as the weather
does.

THEN THE WEAKEST PAIRS. Among half-full sets, the winner keeps the closest passes
furthest apart, then the next closest, and so on (leximin); ties go to the lowest
residues. Exhaustive while a modulus has at most EXHAUSTIVE_LIMIT half-full sets, and
otherwise a local search that says it may have missed the best.

Single-pass voices have no passes to tell apart; their accent only has to complete the
velocity profile. They, and voices whose passes run through different blocks, use the
generic search: the smallest set of up to GENERIC_MOST residues that puts every voice at
its state ceiling.
"""
import itertools
import math

import numpy as np

import config
from accents import duplicate_passes, required_modulus, shared_velocity_levels, velocities_of

EXHAUSTIVE_LIMIT = 2_000_000    # half-full sets for one modulus, tried one by one
GENERIC_LIMIT = 300_000         # candidate sets for the generic search, tried one by one
GENERIC_MOST = 5                # the generic search's largest set


# --------------------------------------------------------------------- what a set does

def span_groups(note_layers, units, parity):
    """Voices grouped by their span accent's modulus. Each modulus gets ONE residue set."""
    groups = {}
    for name, layer in note_layers.items():
        modulus = required_modulus(layer, parity // units[name])
        if modulus is None:
            raise ValueError(f"no modulus makes {name}'s {layer}-step layer span "
                             f"{parity // units[name]} steps; it cannot reach parity")
        groups.setdefault(modulus, []).append(name)
    return groups


def format_residues(residues):
    """`{32: (0, 1, ...), 3: (0,)}`, widest modulus first, as config.py writes it."""
    if not isinstance(residues, dict):
        return str(tuple(residues))
    return '{' + ', '.join(f"{m}: {tuple(residues[m])}"
                           for m in sorted(residues, reverse=True)) + '}'


def try_residues(field, note_layers, residues, names=None):
    """(fields, levels) with every voice built from these residues, or None if the set
    cannot be built or leaves two passes identical in any voice of `names` (all)."""
    try:
        fields = {cfg['name']: field(cfg, residues, quiet=True)
                  for cfg in config.INSTRUMENT_CONFIGS}
        levels = shared_velocity_levels({n: f['accents'] for n, f in fields.items()})
    except ValueError:
        return None
    for name in fields if names is None else names:
        if duplicate_passes(velocities_of(fields[name], levels), note_layers[name]):
            return None
    return fields, levels


def states_used(fields, levels, names=None):
    return {n: len({int(v) for v in velocities_of(fields[n], levels) if v})
            for n in (fields if names is None else names)}


def pass_differences(fields, levels, note_layers, names=None):
    """For each voice, how many steps each pair of its passes differs at."""
    found = {}
    for name in fields if names is None else names:
        velocities = list(velocities_of(fields[name], levels))
        layer = note_layers[name]
        passes = [velocities[i * layer:(i + 1) * layer]
                  for i in range(len(velocities) // layer)]
        found[name] = [sum(1 for a, b in zip(one, other) if a != b)
                       for one, other in itertools.combinations(passes, 2)]
    return found


def weakest_pass_difference(fields, levels, note_layers, names=None):
    """How many steps separate the two most SIMILAR passes anywhere; None if none repeat."""
    every = [d for diffs in pass_differences(fields, levels, note_layers, names).values()
             for d in diffs]
    return min(every) if every else None


def describe_apart(apart):
    """The pass-difference figure in words, or why there is none."""
    if apart is None:
        return "no voice restates its rhythm, so there are no repeats to tell apart"
    return f"the two most similar passes anywhere differ at {apart} steps"


# ------------------------------------------------------------------- half-full search

def pass_blocks(modulus, names, note_layers):
    """(blocks, passes) shared by every voice on this modulus, or None when their
    passes run through different blocks or there is only one pass."""
    sizes = {math.gcd(note_layers[name], modulus) for name in names}
    if len(sizes) != 1:
        return None
    blocks = sizes.pop()
    passes = modulus // blocks
    return (blocks, passes) if passes >= 2 else None


def half_words(passes):
    """Every way to fill half (rounded down) of a block's positions."""
    return [tuple(1 if q in filled else 0 for q in range(passes))
            for filled in itertools.combinations(range(passes), passes // 2)]


def block_contributions(names, binaries, note_layers, modulus, blocks, passes, words):
    """How much each word, in each block, separates each pass pair of each voice.

    Shape (blocks, words, voices x pass pairs). An attack at layer step i lies in block
    i mod `blocks`; pass k reads position q_k of that block; two passes differ at the
    attack when the word's bits at their positions differ.
    """
    pairs = list(itertools.combinations(range(passes), 2))
    table = np.array(words)
    found = np.zeros((blocks, len(words), len(names) * len(pairs)), dtype=np.int32)
    for v, name in enumerate(names):
        layer = note_layers[name]
        for i in np.flatnonzero(binaries[name]):
            block = int(i) % blocks
            positions = [((k * layer + int(i)) % modulus - block) // blocks
                         for k in range(passes)]
            seen = table[:, positions]
            for p, (j, k) in enumerate(pairs):
                found[block, :, v * len(pairs) + p] += seen[:, j] != seen[:, k]
    return found


def residues_of(choice, words, blocks, passes):
    """The residues a choice of one word per block fills."""
    return tuple(sorted(block + blocks * q for block, w in enumerate(choice)
                        for q in range(passes) if words[w][q]))


def leximin_key(vector):
    """Every pass pair's difference, smallest first: compared like words, larger wins."""
    return tuple(sorted(int(x) for x in vector))


def exhaustive_half(contributions, words, blocks, passes):
    """The best half-full set: leximin over every pass pair, then the lowest residues.
    Meet in the middle, the first half of the blocks against the second."""
    dims = contributions.shape[2]

    def combine(chosen_blocks):
        vectors, choices = np.zeros((1, dims), dtype=np.int32), [()]
        for block in chosen_blocks:
            vectors = (vectors[:, None, :] + contributions[block][None, :, :]).reshape(-1, dims)
            choices = [c + (w,) for c in choices for w in range(len(words))]
        return vectors, choices

    middle = blocks // 2
    left, left_choices = combine(range(middle))
    right, right_choices = combine(range(middle, blocks))
    best, winners = None, []
    for a, row in enumerate(left):
        keys = np.sort(row + right, axis=1)
        top = keys[np.lexsort(keys.T[::-1])[-1]]
        key = tuple(int(x) for x in top)
        if best is None or key > best:
            best, winners = key, []
        if key == best:
            winners += [(a, int(r)) for r in np.flatnonzero((keys == top).all(axis=1))]
    candidates = sorted(residues_of(left_choices[a] + right_choices[r], words, blocks, passes)
                        for a, r in winners)
    return candidates[0], best


def local_half(contributions, words, blocks, passes):
    """Too many half-full sets to try: from every block's first word, keep taking the
    single change that most improves the leximin key. Deterministic; may miss the best."""
    choice = [0] * blocks
    vector = sum(contributions[b][0] for b in range(blocks))
    best = leximin_key(vector)
    while True:
        move = None
        for block in range(blocks):
            for w in range(len(words)):
                if w == choice[block]:
                    continue
                trial = vector - contributions[block][choice[block]] + contributions[block][w]
                key = leximin_key(trial)
                if key > (move[0] if move else best):
                    move = (key, block, w, trial)
        if move is None:
            return residues_of(choice, words, blocks, passes), best
        best, block, w, vector = move
        choice[block] = w


def half_residues(modulus, names, binaries, note_layers):
    """(residues, how) for a modulus whose voices restate their layer, or None."""
    structure = pass_blocks(modulus, names, note_layers)
    if structure is None:
        return None
    blocks, passes = structure
    words = half_words(passes)
    contributions = block_contributions(names, binaries, note_layers, modulus,
                                        blocks, passes, words)
    count = len(words) ** blocks
    if count <= EXHAUSTIVE_LIMIT:
        residues, key = exhaustive_half(contributions, words, blocks, passes)
        how = f"half of every block, the best of all {count:,} half-full sets"
    else:
        residues, key = local_half(contributions, words, blocks, passes)
        how = (f"half of every block, found by a local search among {count:,} half-full "
               f"sets — the best it reached, NOT proven the best that exists")
    if key[0] == 0:
        return None                     # no half-full set separates every pass
    return residues, how


# ------------------------------------------------------------------- generic search

def generic_residues(field, note_layers, ceilings, modulus, names, fixed):
    """Sets of up to GENERIC_MOST residues: the one that puts every voice in `names` at
    its ceiling and makes their passes differ most; ties to the smaller set, then the
    lower residues. Above GENERIC_LIMIT candidates, a local search."""
    total = sum(math.comb(modulus, size) for size in range(1, GENERIC_MOST + 1))
    if total > GENERIC_LIMIT:
        return local_generic(field, note_layers, ceilings, modulus, names, fixed, total)
    best = distinct_only = None
    for size in range(1, GENERIC_MOST + 1):
        for candidate in itertools.combinations(range(modulus), size):
            got = try_residues(field, note_layers, {**fixed, modulus: candidate}, names)
            if got is None:
                continue
            fields, levels = got
            used = states_used(fields, levels, names)
            if distinct_only is None:
                distinct_only = (candidate, used)
            if not all(used[n] >= ceilings[n] for n in names):
                continue
            apart = weakest_pass_difference(fields, levels, note_layers, names)
            apart = -1 if apart is None else apart
            if best is None or apart > best[0]:
                best = (apart, candidate)
    if best is None:
        raise ValueError(no_residues_message(distinct_only, ceilings, modulus, GENERIC_MOST))
    return best[1], f"the smallest set of up to {GENERIC_MOST} that completes the profile"


def local_generic(field, note_layers, ceilings, modulus, names, fixed, total):
    """The generic search when trying every set is impractical: one change at a time."""
    cap = max(1, modulus // 2)

    def grade(candidate):
        got = try_residues(field, note_layers, {**fixed, modulus: candidate}, [])
        if got is None:
            return None
        fields, levels = got
        identical = sum(len(duplicate_passes(velocities_of(fields[n], levels), note_layers[n]))
                        for n in names)
        used = states_used(fields, levels, names)
        reached = sum(min(used[n], ceilings[n]) for n in names)
        apart = (weakest_pass_difference(fields, levels, note_layers, names)
                 if not identical else 0)
        return (-identical, reached, apart or 0), used

    singles = [(g, (r,)) for r in range(modulus) if (g := grade((r,))) is not None]
    if not singles:
        raise ValueError(f"no single span residue below {modulus} can be built for this "
                         f"sieve; nothing was written")
    (current_grade, current_used), current = max(singles, key=lambda x: x[0][0])
    for _ in range(4 * cap):
        members, others = set(current), [r for r in range(modulus) if r not in current]
        moves = []
        if len(current) < cap:
            moves += [tuple(sorted(members | {r})) for r in others]
        if len(current) > 1:
            moves += [tuple(sorted(members - {r})) for r in current]
        moves += [tuple(sorted(members - {a} | {b})) for a in current for b in others]
        best_move = None
        for move in moves:
            graded = grade(move)
            if graded and graded[0] > (best_move[0][0] if best_move else current_grade):
                best_move = (graded, move)
        if best_move is None:
            break
        (current_grade, current_used), current = best_move
    identical, reached, _ = current_grade
    if identical or reached < sum(ceilings[n] for n in names):
        short = {n: f"{current_used[n]}/{ceilings[n]}" for n in names
                 if current_used[n] < ceilings[n]}
        raise ValueError(
            f"the exhaustive span search would try {total:,} sets for modulus {modulus}, "
            f"too many, so a local search ran instead and the best it found was {current}: "
            + (f"{-identical} pair(s) of identical passes remain, " if identical else "")
            + (f"voices short of their ceiling {short}. " if short else "")
            + "A local search can miss sets that exist, so this is NOT a proof that none "
              "do. Name SPAN_RESIDUES in config.py to try your own, or change the basic "
              "units. Nothing was written.")
    return current, f"a local search over {total:,} possible sets — NOT proven the best"


def no_residues_message(distinct_only, ceilings, modulus, most):
    """Say WHICH requirement the search could not meet, and claim nothing further.

    No set making every pass distinct is a failure of this bounded SEARCH (capacity was
    already checked). A set that does, but leaves a voice below its state ceiling, fails
    only a selection rule, so it is named for the author to choose.
    """
    searched = f"sets of up to {most} residues below {modulus}"
    if distinct_only is None:
        return (
            f"no span accent among {searched} made every pass of every voice distinct "
            f"— Principle IV unmet. Every voice is within its accent capacity, so this "
            f"is a failure of THIS bounded search at these basic units and this "
            f"weather, not a proof that no residues exist: a wider search, other units "
            f"or a richer accent design may succeed. Nothing was written.")
    candidate, used = distinct_only
    short = {n: f"{used[n]}/{ceilings[n]}" for n in used if used[n] < ceilings[n]}
    return (
        f"Principle IV is satisfiable — SPAN_RESIDUES[{modulus}] = {candidate} makes every "
        f"pass of every voice distinct. What no set among {searched} could also do is "
        f"put every voice at its state ceiling ({short} with that set). That ceiling is "
        f"a selection rule, not a principle. Name those residues in config.py to render "
        f"with them, or widen the search. Nothing was written.")


# --------------------------------------------------------------------------- the whole

def derive_span_residues(field, note_layers, ceilings, units, parity, binaries):
    """One residue set per span modulus: (residues, states used, weakest pair, how).

    Moduli whose voices restate their layer are filled halfway; the rest (single-pass
    voices, mixed blocks, or no half-full set that separates every pass) use the generic
    search with the half-full sets fixed. The whole answer is then checked: no identical
    passes, every voice at its ceiling.
    """
    groups = span_groups(note_layers, units, parity)
    chosen, how, pending = {}, {}, []
    for modulus in sorted(groups, reverse=True):
        found = half_residues(modulus, groups[modulus], binaries, note_layers)
        if found is None:
            pending.append(modulus)
        else:
            chosen[modulus], how[modulus] = found
    for modulus in pending:
        # A placeholder for moduli still to come, so every voice can be built.
        fixed = {**{m: (0,) for m in pending}, **chosen}
        chosen[modulus], how[modulus] = generic_residues(
            field, note_layers, ceilings, modulus, groups[modulus], fixed)

    got = try_residues(field, note_layers, chosen)
    if got is None:
        raise ValueError(f"the span residues {format_residues(chosen)} leave two passes of "
                         f"a voice identical; nothing was written")
    fields, levels = got
    used = states_used(fields, levels)
    short = {n: f"{used[n]}/{ceilings[n]}" for n in used if used[n] < ceilings[n]}
    if short:
        raise ValueError(f"the span residues {format_residues(chosen)} leave voices short "
                         f"of their ceiling: {short}. Nothing was written.")
    return chosen, used, weakest_pass_difference(fields, levels, note_layers), how
