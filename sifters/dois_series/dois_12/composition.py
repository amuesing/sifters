"""dois_twelve — sieve to MIDI.

Differences from dois_ten, all of them guards against silent wrongness:

  * the true period of every sieve is MEASURED, not taken from music21's
    Sieve.period(), which reports the nominal modulus and would let a reducible
    residue set halve a period undetected;
  * the note layer's period is DERIVED from the base sieve rather than declared,
    so the two cannot disagree;
  * unknown duration names RAISE instead of silently yielding a sixteenth;
  * binary derivations dispatch to named operations in transformations.py;
  * every run ends by re-reading the files it wrote and asserting the invariants
    the project actually cares about (see verify()).

New in dois_twelve, for actually producing with:

  * the span accent's MODULUS and RESIDUES are derived from the parity arithmetic
    rather than written down — dois_eleven's 32 and 3 were correct for a 40-step note
    layer and silently wrong for any other;
  * rendering only replaces the files it is about to write, instead of emptying the
    output directory — anything you save or edit there now survives;
  * every track carries a provenance line: sieve, accents, period and a config
    fingerprint, so two renders are never confusable;
  * retrograde and augmentation are available as relationships.
"""
import os
import glob
import hashlib
import math
import sys
from datetime import date
import mido
import music21
import numpy as np
from config import *
from transformations import (invert_binary, reverse_binary, shift_binary,
                             stretch_binary, intersect_binaries, union_binaries)

# ---------------------------------------------------------------------------
# Periods
# ---------------------------------------------------------------------------

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
    """The period a sieve's binary ACTUALLY repeats on.

    `music21.sieve.Sieve.period()` returns the LCM of the moduli written in the
    expression. That is an upper bound, not the truth: `32@0|32@1|32@16|32@17` reports
    32 and repeats every 16, because its residues are themselves periodic. Trusting it
    would let a voice be rendered at twice its real period — the same material stated
    twice and still called one period.

    The true period always divides the nominal one, so evaluating over one nominal
    period and taking the smallest divisor the array repeats on is exact.
    """
    nominal = music21.sieve.Sieve(expression).period()
    measured = minimal_period(evaluate(expression, nominal))
    if measured != nominal:
        print(f"  !! {expression!r} declares modulus {nominal} but truly repeats every "
              f"{measured}. Its residues are reducible; rewrite them or the period "
              f"will be overstated.")
    return measured

# ---------------------------------------------------------------------------
# Timing
# ---------------------------------------------------------------------------

def get_step_ticks(config):
    """Ticks per step. Unknown duration names raise rather than defaulting.

    A silent default here is how the 40/16 meter bug happened in dois_ten: an
    unrecognised value quietly became a sixteenth and nothing downstream could tell.
    """
    if 'step_ticks' in config:
        return config['step_ticks']
    if 'duration' not in config:
        raise KeyError(f"voice {config.get('name')!r} sets neither 'duration' nor "
                       f"'step_ticks'")
    duration = config['duration']
    if duration not in DURATION_MULTIPLIER_KEY:
        raise KeyError(f"voice {config.get('name')!r}: unknown duration {duration!r}. "
                       f"Known: {sorted(DURATION_MULTIPLIER_KEY)}. A triplet or other "
                       f"non-power-of-two grid must set 'step_ticks' directly.")
    return int(TICKS_PER_QUARTER_NOTE * DURATION_MULTIPLIER_KEY[duration])

def meter_for(bar_ticks, denominators=(16, 8, 4, 32, 2, 64, 1)):
    """A meter whose bar is exactly `bar_ticks`, or None."""
    for den in denominators:
        beat_ticks = (4 * TICKS_PER_QUARTER_NOTE) / den
        if beat_ticks != int(beat_ticks):
            continue
        beat_ticks = int(beat_ticks)
        if bar_ticks % beat_ticks == 0:
            numerator = bar_ticks // beat_ticks
            if 1 <= numerator <= MAX_METER_NUMERATOR:
                return numerator, den
    return None

def meter_for_voice(step_ticks, note_layer_ticks, period_ticks):
    """A meter in which this voice's clip ends exactly on a bar line.

    Preference 1 — the beat IS the voice's basic unit and the bar is one pass of the
    note layer. A sixteenth grid gives 4*TPQ/120 = 16, so 40 steps is 40/16.

    Preference 2 — a grid that is not a power-of-two subdivision cannot be a beat
    (a triplet gives 4*TPQ/160 = 12, not a valid denominator). Fall back to any meter
    whose BAR equals the voice's whole period: the beat is then not the voice's unit,
    but the bar still lands on the period, which is what stops a host padding the clip.
    """
    denominator = (4 * TICKS_PER_QUARTER_NOTE) / step_ticks
    if denominator == int(denominator) and not (int(denominator) & (int(denominator) - 1)):
        numerator = note_layer_ticks // step_ticks
        if 1 <= numerator <= MAX_METER_NUMERATOR:
            return int(numerator), int(denominator)
    return meter_for(period_ticks, denominators=(4, 8, 16, 2, 32, 1, 64))

def shared_meter(lengths, candidate_bars):
    """One meter for every voice, when one exists.

    A candidate bar is one pass of SOME voice's note layer at that voice's own basic
    unit. Voices may have different note layers and different units, so each offers a
    different candidate. One can be shared only if it divides EVERY length — otherwise
    a clip would not end on a bar line and the host would pad it — and is expressible
    as a meter at all. The finest workable bar wins, so the beat stays a real
    subdivision rather than a coarse container.
    """
    for bar in sorted(set(candidate_bars)):
        if any(length % bar for length in lengths):
            continue
        meter = meter_for(bar)
        if meter:
            return meter
    return None

def config_fingerprint():
    """A short hash of everything that determines the output.

    Two renders with different sieves, accents, units, tempo or meter get different
    fingerprints; two renders of the same configuration get the same one. Without it,
    files from different versions are indistinguishable once they are sitting in a
    project folder.
    """
    parts = [INSTRUMENT_CONFIGS[0].get('sieve', ''), repr(sorted(WEATHER.items())),
             repr(SPAN_RESIDUE_SOURCE), str(TEMPO_BPM), str(TICKS_PER_QUARTER_NOTE),
             repr([(c['name'], c.get('relationship'), c.get('shift_amount'),
                    c.get('factor'), c.get('duration'), c.get('step_ticks'), c['root'])
                   for c in INSTRUMENT_CONFIGS])]
    return hashlib.sha256("|".join(parts).encode()).hexdigest()[:8]

def append_header(track, name, meter, provenance=None):
    track.append(mido.MetaMessage('track_name', name=name, time=0))
    if provenance:
        track.append(mido.MetaMessage('text', text=provenance, time=0))
    numerator, denominator = meter
    track.append(mido.MetaMessage('time_signature', numerator=numerator,
                                  denominator=denominator, time=0))
    track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(TEMPO_BPM), time=0))

# ---------------------------------------------------------------------------
# Binary construction
# ---------------------------------------------------------------------------

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

def voice_rhythm(config, base_binaries, span):
    """A voice's note layer across its full span.

    A voice defined by a sieve is EVALUATED over the span rather than tiled, so no
    assumption about its period is relied on. A derived voice applies its operation to
    its sources tiled across the same span — exact, because `tile_to` refuses a span
    the note layer does not divide.
    """
    if 'sieve' in config:
        return evaluate(config['sieve'], span)

    derives_from = config['derives_from']
    if isinstance(derives_from, str):
        derives_from = [derives_from]
    sources = [tile_to(base_binaries[n], span) for n in derives_from]
    return RELATIONSHIPS[config['relationship']](sources, config)

def sources_for(config, base_binaries):
    """The source note layers a derived voice combines, tiled to a common length.

    Sources need not share a period. Two sieves of period 40 and 35 are both defined
    over LCM(40, 35) = 280 steps, and that is where their intersection or union lives.
    Tiling each to the LCM is the only way to combine them without misaligning one.
    """
    derives_from = config['derives_from']
    if isinstance(derives_from, str):
        derives_from = [derives_from]
    missing = [n for n in derives_from if n not in base_binaries]
    if missing:
        raise ValueError(f"voice {config.get('name')!r} derives from {missing}, which "
                         f"is not defined before it")

    sources = [base_binaries[n] for n in derives_from]
    common = math.lcm(*(len(s) for s in sources))
    return [tile_to(s, common) for s in sources]

def build_binary(config, base_binaries):
    """One voice's note layer, at its OWN true period.

    Every voice derives its own period; they happen to coincide here because all four
    descend from one 40-step sieve, but nothing assumes that. A voice defined by its
    own sieve takes that sieve's measured period. A derived voice is combined over the
    LCM of its sources' periods, then reduced to the period the result actually has —
    a derivation can close sooner than its sources do, and the voice's length must state
    the period it really has, not the one it was computed over.
    """
    if 'sieve' in config:
        period = true_period(config['sieve'])
        return evaluate(config['sieve'], period), period

    relationship = config.get('relationship')
    if relationship not in RELATIONSHIPS:
        raise ValueError(f"voice {config.get('name')!r}: unknown relationship "
                         f"{relationship!r}. Known: {sorted(RELATIONSHIPS)}")

    result = RELATIONSHIPS[relationship](sources_for(config, base_binaries), config)
    period = minimal_period(result)
    return result[:period], period

# ---------------------------------------------------------------------------
# Accent voicing
# ---------------------------------------------------------------------------

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

def span_accent(note_layer, target_span):
    """The span accent for a voice: modulus AND residues, both derived.

    The modulus follows from the parity arithmetic (see `required_modulus`). The
    residues are SPAN_RESIDUE_SOURCE — clause 1's mod-8 residues — kept where they fall
    below that modulus. `sieve8` is clauses 2+3, so clause 1 is exactly the clause the
    weather omits, which is also what keeps the span accent independent of `sieve8`
    rather than a refinement of it.

    At modulus 32 that gives {0,1,7}; at modulus 3, {0,1}. Both are what dois_eleven had
    written by hand.
    """
    modulus = required_modulus(note_layer, target_span)
    if modulus is None:
        raise ValueError(f"no modulus makes a {note_layer}-step layer span "
                         f"{target_span} steps; this voice cannot reach parity")
    residues = sorted(r for r in SPAN_RESIDUE_SOURCE if r < modulus)
    if not residues:
        raise ValueError(f"modulus {modulus} is too small for any residue in "
                         f"{SPAN_RESIDUE_SOURCE}")
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

def accent_voicing(binary, accent_binaries, profile, root_note):
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
        notes_per_step[i] = [root_note]
    return notes_per_step, velocities

# ---------------------------------------------------------------------------
# MIDI rendering
# ---------------------------------------------------------------------------
# A per-voice file is EXACTLY ONE period of that voice, at its own basic unit. Voices
# on different units, or with different accent spans, therefore have different lengths
# — correct, not a defect.
#
# Ensemble files repeat each voice a WHOLE number of its own periods, enough for every
# voice to finish together. A period is never stretched or truncated to fit, so one
# cycle inside an ensemble file equals that voice's own file exactly — which is what
# makes the per-voice files usable to check the ensemble.

def gate_ticks(step_ticks):
    """How long a note sounds: a fraction of its step, never the whole step.

    A full-step gate ends a note on the tick the next begins, which many sustaining
    instruments will not re-articulate from. At least one tick of silence is guaranteed.
    """
    gate = int(round(step_ticks * GATE_RATIO))
    return max(1, min(gate, step_ticks - 1))

def voice_events(notes_per_step, velocities, step_ticks, total_ticks):
    """Absolute-time (tick, kind, pitch, velocity); kind 1 = note_on, 0 = note_off."""
    active = np.flatnonzero(velocities)
    if active.size == 0:
        return []
    cycle_ticks = len(velocities) * step_ticks
    if total_ticks % cycle_ticks:
        raise ValueError(f"{total_ticks} is not a whole number of {cycle_ticks}-tick "
                         f"cycles; a voice would be cut mid-period")
    events = []
    for rep in range(total_ticks // cycle_ticks):
        rep_start = rep * cycle_ticks
        for idx in active:
            on_tick = rep_start + int(idx) * step_ticks
            velocity = int(velocities[idx])
            for pitch in notes_per_step[idx]:
                events.append((on_tick,                       1, int(pitch), velocity))
                events.append((on_tick + gate_ticks(step_ticks), 0, int(pitch), 0))
    return events

def make_track(name, events, total_ticks, meter, provenance=None):
    track = mido.MidiTrack()
    append_header(track, name, meter, provenance)

    # note_off (kind 0) sorts ahead of note_on at the same tick, so a pitch that
    # retriggers on consecutive steps releases before it strikes again.
    prev = 0
    for abs_tick, kind, pitch, vel in sorted(events, key=lambda e: (e[0], e[1])):
        track.append(mido.Message('note_on' if kind == 1 else 'note_off',
                                  note=pitch, velocity=vel, time=abs_tick - prev))
        prev = abs_tick

    if prev > total_ticks:
        raise ValueError(f"track {name!r} has events past its {total_ticks}-tick end")
    # Pad to the true boundary so the host reads the correct clip length rather than
    # stopping at the last note.
    track.append(mido.MetaMessage('end_of_track', time=total_ticks - prev))
    return track

def save_tracks(tracks, filename, total_ticks, meter, note=''):
    if not tracks:
        print(f"  Skipped {filename}: no tracks")
        return
    mid = mido.MidiFile(ticks_per_beat=TICKS_PER_QUARTER_NOTE)
    mid.tracks.extend(tracks)

    numerator, denominator = meter
    bar_ticks = numerator * (4 * TICKS_PER_QUARTER_NOTE) // denominator
    warning = "" if total_ticks % bar_ticks == 0 else "  <-- NOT whole bars, host will pad"
    try:
        mid.save(os.path.join(OUTPUT_DIR, f"{filename}.mid"))
        print(f"  Saved: {filename}.mid  ({total_ticks} ticks = "
              f"{total_ticks / bar_ticks:g} bars of {numerator}/{denominator}{note})"
              f"{warning}")
    except OSError as e:
        raise RuntimeError(f"could not save {filename}: {e}") from e

# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------
# Every bug this project has hit was found by reading the rendered MIDI back and
# checking an invariant — and then the script that did it was thrown away, so the
# next regression went unnoticed until someone looked again. These checks run on
# every render, against the bytes on disk, not against the values in memory.

def read_track(path, track_index=None, pitch=None):
    """(onset, duration, pitch, velocity) for a file, one track, or one pitch."""
    notes, hanging, overlaps = [], [], []
    midi = mido.MidiFile(path)
    for i, track in enumerate(midi.tracks):
        if track_index is not None and i != track_index:
            continue
        t, open_notes = 0, {}
        for msg in track:
            t += msg.time
            if msg.type == 'note_on' and msg.velocity > 0:
                if msg.note in open_notes:
                    overlaps.append((msg.note, t))
                open_notes[msg.note] = (t, msg.velocity)
            elif msg.type in ('note_off', 'note_on') and msg.note in open_notes:
                onset, vel = open_notes.pop(msg.note)
                if pitch is None or msg.note == pitch:
                    notes.append((onset, t - onset, msg.note, vel))
        hanging.extend(open_notes)
    return sorted(notes), hanging, overlaps

def track_meta(path):
    """[(name, (num, den), tempo, end_tick)] per track."""
    out = []
    for track in mido.MidiFile(path).tracks:
        t, name, sig, tempo = 0, None, None, None
        for msg in track:
            t += msg.time
            if msg.type == 'track_name':
                name = msg.name
            elif msg.type == 'time_signature':
                sig = (msg.numerator, msg.denominator)
            elif msg.type == 'set_tempo':
                tempo = msg.tempo
        out.append((name, sig, tempo, t))
    return out

def rhythm_from_file(path, step_ticks, note_layer_steps):
    """Read a voice's note layer back out of its rendered file.

    Returns the note layer, and whether the file is genuinely periodic on it — if the
    rendered onsets do not repeat every `note_layer_steps`, the file is not a tiling of
    the sieve at all and the derivation check below would be meaningless.
    """
    notes, _, _ = read_track(path)
    total = max(o + d for o, d, _, _ in notes)
    grid = np.zeros(-(-total // step_ticks), dtype=int)
    for onset, _, _, _ in notes:
        grid[onset // step_ticks] = 1
    layer = grid[:note_layer_steps]
    periodic = all(grid[i] == layer[i % note_layer_steps] for i in range(len(grid)))
    return layer, periodic

def check_derivations(base_binaries):
    """Assert every voice really is what config says it is derived from.

    This is the one class of error the file-level checks cannot see. Change
    `shift_amount` to 14, or swap `intersection` for `union`, and every clip is still
    one true period, still ends on a bar line, still matches its ensemble track — and
    the piece is no longer the structure it claims to be. The project's whole premise
    is that voices are DERIVED rather than independently authored, so the derivations
    are what must be checked.
    """
    problems = []
    for cfg in INSTRUMENT_CONFIGS:
        name = cfg['name']
        got = base_binaries[name]
        if 'sieve' in cfg:
            want = evaluate(cfg['sieve'], len(got))
            if not np.array_equal(got, want):
                problems.append(f"{name}: does not match its own sieve expression")
            continue

        derives_from = cfg['derives_from']
        if isinstance(derives_from, str):
            derives_from = [derives_from]
        sources = sources_for(cfg, base_binaries)
        want = RELATIONSHIPS[cfg['relationship']](sources, cfg)
        want = want[:minimal_period(want)]
        rel = cfg['relationship']
        if not np.array_equal(got, want):
            problems.append(f"{name}: is not the {rel} of {derives_from}")
            continue

        # The relationships also carry structural promises worth stating outright.
        if rel == 'complement':
            src = tile_to(sources[0], len(got)) if len(sources[0]) != len(got) else sources[0]
            if (got & src).any():
                problems.append(f"{name}: overlaps {derives_from[0]}, so it is not a complement")
            if not (got | src).all():
                problems.append(f"{name}: with {derives_from[0]} leaves gaps; a complement "
                                f"pair must cover every step")
        elif rel == 'shift':
            if cfg['shift_amount'] % len(got) == 0:
                problems.append(f"{name}: shift of {cfg['shift_amount']} is a whole number "
                                f"of periods — it is a copy, not a canon")
        elif rel == 'intersection':
            if not got.any():
                problems.append(f"{name}: the intersection is empty — the voice is silent")
    return problems

def verify(voices, periods, total_ticks, note_layers, base_binaries):
    """Re-read every written file and assert what the project actually promises."""
    failures = []
    def check(condition, message):
        if not condition:
            failures.append(message)
        return condition

    print("\nVerifying the rendered files:")
    steps = {name: len(vel) for name, _, vel, _ in voices}
    pads  = {cfg['name']: cfg['root'] for cfg in INSTRUMENT_CONFIGS}

    # --- the principles, before anything about the files -------------------
    for problem in check_derivations(base_binaries):
        failures.append(problem)

    # PARITY. Not a preference: "all voices begin and end together" plus "nothing
    # repeats identically" jointly require it. If periods differed, the cycle where
    # they align would be their LCM — longer than the shortest voice, which would then
    # repeat inside it.
    spans = set(periods.values())
    check(len(spans) == 1,
          f"voices do not share a period: {periods}. The ensemble would then be their "
          f"LCM and the shorter voices would repeat inside it.")
    if len(spans) == 1:
        print(f"  parity: every voice is {spans.pop()} ticks")

    # ONE WEATHER. Every voice must carry the shared accent set. Exactly one accent may
    # differ — the parity accent, whose only job is to set the period, and which cannot
    # be shared across grids without breaking parity.
    sets = {cfg['name']: set(cfg['accent_dict']) for cfg in INSTRUMENT_CONFIGS}
    common = set.intersection(*sets.values())
    for name, own in sets.items():
        check(set(WEATHER) <= own, f"{name}: missing shared weather {set(WEATHER) - own}")
        extra = own - set(WEATHER)
        check(len(extra) == 1,
              f"{name}: carries {len(extra)} accents outside the weather ({extra}); "
              f"only the span accent may differ")
    print(f"  one weather: {sorted(common)} shared by all; "
          f"span accent differs by grid ({', '.join(sorted(n + '=' + next(iter(s - set(WEATHER))) for n, s in sets.items()))})")

    # NO ABSOLUTE REPETITION. The minimal-period check below catches repetition at a
    # divisor of the span, but two arbitrary passes could still coincide without making
    # the whole sequence periodic. Compare every pass against every other.
    for name, _, velocities, step_ticks in voices:
        layer = note_layers[name]
        n_passes = len(velocities) // layer
        passes = [tuple(velocities[i * layer:(i + 1) * layer]) for i in range(n_passes)]
        dupes = [(i + 1, j + 1) for i in range(n_passes) for j in range(i + 1, n_passes)
                 if passes[i] == passes[j]]
        check(not dupes,
              f"{name}: passes {dupes} of the note layer are identical — the accent "
              f"field failed to inflect them, so the repetition parity requires is bare")
        if not dupes:
            print(f"  {name}: {n_passes} passes of its note layer, all distinct")
    if not failures:
        rels = ", ".join(
            f"{c['name']}={c.get('relationship', 'base sieve')}" for c in INSTRUMENT_CONFIGS)
        print(f"  derivations intact: {rels}")

    # --- per-voice files -------------------------------------------------
    for name, _, velocities, step_ticks in voices:
        path = os.path.join(OUTPUT_DIR, f"{TITLE}_{name}_prime.mid")
        (nm, sig, tempo, end), = track_meta(path)
        notes, hanging, overlaps = read_track(path)

        check(end == periods[name],
              f"{name}: file is {end} ticks, its period is {periods[name]}")
        check(not hanging, f"{name}: {len(hanging)} hanging note(s)")
        check(not overlaps, f"{name}: {len(overlaps)} same-pitch overlap(s)")
        gate = gate_ticks(step_ticks)
        check(all(d == gate for _, d, _, _ in notes),
              f"{name}: not every note is {gate} ticks (gate) long")
        check(gate < step_ticks,
              f"{name}: gate {gate} fills the whole {step_ticks}-tick step, so notes abut")

        # No two notes on a pitch may touch: a zero-length gap is where a sustaining
        # instrument fails to re-articulate and a sieve hit goes unheard.
        seq = sorted((o, o + d) for o, d, _, _ in notes)
        touching = [(a, b) for (_, a), (b, _) in zip(seq, seq[1:]) if a >= b]
        check(not touching,
              f"{name}: {len(touching)} note(s) start where the previous ends")
        check(all(o % step_ticks == 0 for o, _, _, _ in notes),
              f"{name}: some onsets are off the {step_ticks}-tick grid")
        check({p for _, _, p, _ in notes} == {pads[name]},
              f"{name}: expected pitch {pads[name]}")
        check(min(v for _, _, _, v in notes) >= MIN_VELOCITY,
              f"{name}: a hit has velocity below {MIN_VELOCITY}; MIDI reads velocity 0 "
              f"as a note-off, so the note would vanish rather than sound")

        # The rendered rhythm must be the note layer the sieve actually produces.
        layer, periodic = rhythm_from_file(path, step_ticks, note_layers[name])
        check(periodic,
              f"{name}: onsets are not periodic on its {note_layers[name]}-step note layer")
        if periodic:
            check(np.array_equal(layer, base_binaries[name]),
                  f"{name}: the rendered rhythm is not the sieve's note layer")

        bar = sig[0] * (4 * TICKS_PER_QUARTER_NOTE) // sig[1]
        check(end % bar == 0,
              f"{name}: {end} ticks is not whole bars of {sig[0]}/{sig[1]} — host will pad")
        check(tempo == mido.bpm2tempo(TEMPO_BPM), f"{name}: tempo is not {TEMPO_BPM} BPM")

        # the file must be ONE period: not a repeat of something shorter, not a cut
        grid = [0] * (end // step_ticks)
        for onset, _, _, vel in notes:
            grid[onset // step_ticks] = vel
        measured = minimal_period(grid)
        check(measured == steps[name],
              f"{name}: file spans {steps[name]} steps but the pattern repeats every "
              f"{measured} — it is {steps[name] // measured} copies, not one period")
        print(f"  {name}: {len(notes):>3} notes, {end} ticks, {steps[name]} steps, "
              f"{sig[0]}/{sig[1]}, minimal period {measured}")

    # --- ensemble files --------------------------------------------------
    arrangement = os.path.join(OUTPUT_DIR, f"{TITLE}_arrangement.mid")
    drumrack    = os.path.join(OUTPUT_DIR, f"{TITLE}_drumrack.mid")
    index = {nm: i for i, (nm, _, _, _) in enumerate(track_meta(arrangement))}

    for path in (arrangement, drumrack):
        for nm, sig, tempo, end in track_meta(path):
            check(end == total_ticks,
                  f"{os.path.basename(path)} track {nm!r}: {end} ticks, expected {total_ticks}")
            bar = sig[0] * (4 * TICKS_PER_QUARTER_NOTE) // sig[1]
            check(end % bar == 0,
                  f"{os.path.basename(path)} track {nm!r}: not whole bars")

    # every cycle inside the ensemble must equal that voice's own file
    for name, _, _, _ in voices:
        own, _, _ = read_track(os.path.join(OUTPUT_DIR, f"{TITLE}_{name}_prime.mid"))
        arr, _, _ = read_track(arrangement, track_index=index[name])
        drum, _, _ = read_track(drumrack, pitch=pads[name])
        period, reps = periods[name], total_ticks // periods[name]
        check(total_ticks % period == 0, f"{name}: ensemble is not whole cycles")
        for rep in range(reps):
            lo = rep * period
            fold = lambda ns: sorted((o - lo, d, p, v) for o, d, p, v in ns
                                     if lo <= o < lo + period)
            check(fold(arr) == own, f"{name}: arrangement cycle {rep + 1} differs from its file")
            check(fold(drum) == own, f"{name}: drum rack cycle {rep + 1} differs from its file")
        print(f"  {name}: {reps} cycle(s) in both ensemble files, each identical to its file")

    if failures:
        print(f"\n  FAILED — {len(failures)} problem(s):")
        for f in failures:
            print(f"    - {f}")
        return False
    print(f"\n  All checks passed.")
    return True

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def clear_our_outputs(filenames):
    """Remove only the files this run will write.

    dois_eleven emptied the whole output directory, which destroyed anything saved or
    edited there. Only our own filenames are replaced; everything else is left alone
    and reported.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    ours = {f"{name}.mid" for name in filenames}
    for path in glob.glob(os.path.join(OUTPUT_DIR, '*.mid')):
        if os.path.basename(path) in ours:
            os.remove(path)
    kept = sorted(os.path.basename(p) for p in glob.glob(os.path.join(OUTPUT_DIR, '*.mid')))
    if kept:
        print(f"  leaving {len(kept)} other file(s) in mid/ untouched: {', '.join(kept)}")

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Every voice derives its OWN note-layer period — measured, never declared. They
    # coincide here because all four descend from one 40-step sieve, but nothing assumes
    # it: an independent sieve of another period, or a derivation that closes sooner than
    # its sources, would simply carry its own.
    base_binaries, note_layers = {}, {}
    for cfg in INSTRUMENT_CONFIGS:
        binary, period = build_binary(cfg, base_binaries)
        base_binaries[cfg['name']] = binary
        note_layers[cfg['name']] = period

    distinct = sorted(set(note_layers.values()))
    print("Note layers (each derived from that voice's own sieve): "
          + ", ".join(f"{n} {p}" for n, p in note_layers.items())
          + (f"  — all {distinct[0]} steps\n" if len(distinct) == 1
             else f"  — {len(distinct)} different periods in play\n"))
    print("Densities:")
    for cfg in INSTRUMENT_CONFIGS:
        b = base_binaries[cfg['name']]
        print(f"  {cfg['name']}: {b.sum()}/{len(b)} steps ({100 * b.mean():.1f}%)")

    # The parity point, and from it every voice's span accent. Nothing here is chosen:
    # P is the first moment all voices converge, each voice must restate its rhythm
    # P/(layer x unit) times to reach it, and the span accent must be exactly long
    # enough to inflect those restatements.
    units = {}
    for cfg in INSTRUMENT_CONFIGS:
        units[cfg['name']] = get_step_ticks(cfg)
    parity = math.lcm(*(note_layers[n] * units[n] for n in note_layers))
    print(f"\nParity — the first convergence of the raw rhythms:")
    for n in note_layers:
        raw = note_layers[n] * units[n]
        print(f"  {n}: {note_layers[n]} steps x {units[n]} = {raw} ticks, "
              f"restated {parity // raw}x to reach parity")
    print(f"  P = LCM = {parity} ticks = {parity / (TICKS_PER_QUARTER_NOTE * 4):g} bars\n")

    for cfg in INSTRUMENT_CONFIGS:
        name = cfg['name']
        label, expression = span_accent(note_layers[name], parity // units[name])
        cfg['accent_dict'] = dict(WEATHER, **{label: expression})
        print(f"  {name}: span accent derived — modulus {true_period(expression)}, "
              f"{expression}")

    print()
    voices = []
    for cfg in INSTRUMENT_CONFIGS:
        name = cfg['name']
        accent_dict = cfg['accent_dict']
        binary = base_binaries[name]
        step_ticks = units[name]

        span = voice_span(note_layers[name], accent_dict)
        binary_full = voice_rhythm(cfg, base_binaries, span)
        accent_bins = create_accent_binaries(accent_dict, span)
        if cfg.get('relationship') == 'shift':
            accent_bins = {k: np.roll(v, cfg['shift_amount'])
                           for k, v in accent_bins.items()}

        profile = generate_velocity_profile(accent_bins)
        used = sorted(set(profile['levels'].values()))
        gaps = {b - a for a, b in zip(used, used[1:])}
        spacing = str(gaps.pop()) if len(gaps) == 1 else f"{min(gaps)}-{max(gaps)}"
        order = " < ".join(sorted(profile['rarity'], key=profile['rarity'].get))
        print(f"  {name}: rhythm {note_layers[name]} steps, accents span {span} "
              f"({span // note_layers[name]} passes) — {len(used)} levels "
              f"{used[0]}-{used[-1]} spaced {spacing}, rarity order {order}")

        notes_per_step, velocities = accent_voicing(binary_full, accent_bins,
                                                    profile, cfg['root'])
        voices.append((name, notes_per_step, velocities, step_ticks))

    periods = {name: len(vel) * st for name, _, vel, st in voices}
    total_ticks = math.lcm(*periods.values())

    print(f"\n  Voice periods (one full statement at that voice's basic unit):")
    for name, _, velocities, step_ticks in voices:
        print(f"    {name}: {len(velocities)} steps x {step_ticks} ticks = {periods[name]}")
    print(f"  Ensemble {total_ticks} ticks — "
          + ", ".join(f"{n} x{total_ticks // p}" for n, p in periods.items()))

    # Each voice offers one candidate bar: a pass of its own note layer at its own unit.
    candidate_bars = [note_layers[name] * st for name, _, _, st in voices]
    one = shared_meter(list(periods.values()) + [total_ticks], candidate_bars)
    if one:
        bar = one[0] * (4 * TICKS_PER_QUARTER_NOTE) // one[1]
        print(f"\n  Shared meter {one[0]}/{one[1]} (bar {bar} ticks) — "
              + ", ".join(f"{n} {p // bar} bars" for n, p in periods.items()))
        meters = {name: one for name in periods}
    else:
        print("\n  No single meter fits every period; using per-voice meters.")
        meters = {}
        for name, _, _, step_ticks in voices:
            m = meter_for_voice(step_ticks, note_layers[name] * step_ticks, periods[name])
            if m is None:
                m = TIME_SIGNATURE
                print(f"  !! {name}: no meter lands on {periods[name]} ticks — "
                      f"falling back to {m[0]}/{m[1]}; a host will pad this clip.")
            meters[name] = m

    fingerprint = config_fingerprint()
    stamp = (f"{TITLE} {date.today().isoformat()} cfg={fingerprint} "
             f"parity={parity} tempo={TEMPO_BPM} "
             f"weather={'+'.join(WEATHER)} sieve={INSTRUMENT_CONFIGS[0]['sieve']}")
    print(f"\n  provenance stamped on every track: cfg={fingerprint}")

    names = [f"{TITLE}_{n}_prime" for n in periods] + [f"{TITLE}_arrangement",
                                                       f"{TITLE}_drumrack"]
    clear_our_outputs(names)

    print()
    arrangement, merged = [], []
    for name, notes_per_step, velocities, step_ticks in voices:
        events = voice_events(notes_per_step, velocities, step_ticks, periods[name])
        line = f"{stamp} voice={name} accents={'+'.join(dict(zip([c['name'] for c in INSTRUMENT_CONFIGS], INSTRUMENT_CONFIGS))[name]['accent_dict'])}"
        save_tracks([make_track(name, events, periods[name], meters[name], line)],
                    f"{TITLE}_{name}_prime", periods[name], meters[name])
        repeated = voice_events(notes_per_step, velocities, step_ticks, total_ticks)
        arrangement.append(make_track(name, repeated, total_ticks, meters[name], line))
        merged.extend(repeated)

    ensemble_meter = one or meter_for(min(candidate_bars)) or TIME_SIGNATURE
    print()
    reps = ", ".join(f"{n} x{total_ticks // p}" for n, p in periods.items())
    save_tracks(arrangement, f"{TITLE}_arrangement", total_ticks, ensemble_meter,
                note=f", {len(arrangement)} tracks — {reps}")
    save_tracks([make_track(f"{TITLE} drum rack", merged, total_ticks, ensemble_meter,
                            f"{stamp} all voices")],
                f"{TITLE}_drumrack", total_ticks, ensemble_meter,
                note=", all voices on one track")

    if not verify(voices, periods, total_ticks, note_layers, base_binaries):
        sys.exit(1)

if __name__ == '__main__':
    main()
