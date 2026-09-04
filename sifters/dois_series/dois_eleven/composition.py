"""dois_eleven — sieve to MIDI.

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
"""
import os
import glob
import math
import sys
import mido
import music21
import numpy as np
from config import *
from transformations import (invert_binary, shift_binary,
                             intersect_binaries, union_binaries)

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

def shared_meter(lengths, note_layer_ticks):
    """One meter for every voice, when one exists.

    The natural bar is one pass of the note layer at the finest basic unit. It can be
    shared only if EVERY length is a whole number of those bars — otherwise some clip
    would not end on a bar line and the host would pad it.
    """
    if any(length % note_layer_ticks for length in lengths):
        return None
    return meter_for(note_layer_ticks)

def append_header(track, name, meter):
    track.append(mido.MetaMessage('track_name', name=name, time=0))
    numerator, denominator = meter
    track.append(mido.MetaMessage('time_signature', numerator=numerator,
                                  denominator=denominator, time=0))
    track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(TEMPO_BPM), time=0))

# ---------------------------------------------------------------------------
# Binary construction
# ---------------------------------------------------------------------------

RELATIONSHIPS = {
    'complement':   lambda sources, cfg: invert_binary(sources[0]),
    'shift':        lambda sources, cfg: shift_binary(sources[0], cfg['shift_amount']),
    'intersection': lambda sources, cfg: intersect_binaries(sources),
    'union':        lambda sources, cfg: union_binaries(sources),
}

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

def build_binary(config, base_binaries):
    """One voice's note layer, over exactly one period of its own sieve."""
    if 'sieve' in config:
        period = true_period(config['sieve'])
        return evaluate(config['sieve'], period), period

    relationship = config.get('relationship')
    if relationship not in RELATIONSHIPS:
        raise ValueError(f"voice {config.get('name')!r}: unknown relationship "
                         f"{relationship!r}. Known: {sorted(RELATIONSHIPS)}")

    derives_from = config['derives_from']
    if isinstance(derives_from, str):
        derives_from = [derives_from]
    missing = [n for n in derives_from if n not in base_binaries]
    if missing:
        raise ValueError(f"voice {config.get('name')!r} derives from {missing}, which "
                         f"is not defined before it")

    sources = [base_binaries[n] for n in derives_from]
    if len({len(s) for s in sources}) != 1:
        raise ValueError(f"voice {config.get('name')!r}: sources have different lengths "
                         f"{[len(s) for s in sources]}; they must share a period")

    result = RELATIONSHIPS[relationship](sources, config)
    return result, len(result)

# ---------------------------------------------------------------------------
# Accent voicing
# ---------------------------------------------------------------------------

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

def generate_velocity_profile(accent_binaries):
    """Velocity is a weighted SUM of the accents firing — not a count of them.

    An accent's weight is how rarely it fires, proportional to (1 - density). An accent
    covering two thirds of the steps carries almost no information and should barely
    lift a note; a sparse one is genuinely an accent. One firing on every step would
    earn weight 0, which is correct — it says nothing.

    Levels run from GHOST_VELOCITY (no accent, but still audible — the sieve selected
    that step, so it must sound) up to FULL_VELOCITY when every accent agrees.

    Counting overlaps instead throws away WHICH accents fired: four accents have 16
    combinations but only 5 counts, and with dense sieves those counts bunch around
    their mean. It also leaves a sparse accent inaudible unless it fires alone.
    """
    if not accent_binaries:
        return {'ghost': UNACCENTED_VELOCITY, 'weights': {}}

    rarity = {label: 1.0 - float(np.mean(arr)) for label, arr in accent_binaries.items()}
    total = sum(rarity.values()) or 1.0
    budget = FULL_VELOCITY - GHOST_VELOCITY
    weights = {label: int(round(budget * r / total)) for label, r in rarity.items()}

    # Rounding can miss the budget; settle the difference on the heaviest accent so
    # every accent firing together still reaches exactly FULL.
    drift = budget - sum(weights.values())
    if drift:
        weights[max(weights, key=weights.get)] += drift
    return {'ghost': GHOST_VELOCITY, 'weights': weights}

def accent_voicing(binary, accent_binaries, profile, root_note):
    binary = np.asarray(binary)
    n = len(binary)
    on = binary.astype(bool)

    for label, arr in accent_binaries.items():
        if len(arr) != n:
            raise RuntimeError(f"accent {label!r} has {len(arr)} steps, voice has {n}")

    # Ghost floor plus each firing accent's own weight, so WHICH accents are present
    # matters rather than merely how many.
    level = np.full(n, profile['ghost'], dtype=int)
    for label, weight in profile['weights'].items():
        level += weight * accent_binaries[label].astype(int)

    velocities = np.zeros(n, dtype=int)
    velocities[on] = np.clip(level[on], 1, 127)

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
                events.append((on_tick,              1, int(pitch), velocity))
                events.append((on_tick + step_ticks, 0, int(pitch), 0))
    return events

def make_track(name, events, total_ticks, meter):
    track = mido.MidiTrack()
    append_header(track, name, meter)

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

def check_derivations(base_binaries, note_layer_steps):
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
        sources = [base_binaries[n] for n in derives_from]
        want = RELATIONSHIPS[cfg['relationship']](sources, cfg)
        rel = cfg['relationship']
        if not np.array_equal(got, want):
            problems.append(f"{name}: is not the {rel} of {derives_from}")
            continue

        # The relationships also carry structural promises worth stating outright.
        if rel == 'complement':
            src = sources[0]
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

def verify(voices, periods, total_ticks, note_layer_steps, base_binaries):
    """Re-read every written file and assert what the project actually promises."""
    failures = []
    def check(condition, message):
        if not condition:
            failures.append(message)
        return condition

    print("\nVerifying the rendered files:")
    steps = {name: len(vel) for name, _, vel, _ in voices}
    pads  = {cfg['name']: cfg['root'] for cfg in INSTRUMENT_CONFIGS}

    # --- the derivations, before anything about the files -----------------
    for problem in check_derivations(base_binaries, note_layer_steps):
        failures.append(problem)
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
        check(all(d == step_ticks for _, d, _, _ in notes),
              f"{name}: not every note is exactly one {step_ticks}-tick step")
        check(all(o % step_ticks == 0 for o, _, _, _ in notes),
              f"{name}: some onsets are off the {step_ticks}-tick grid")
        check({p for _, _, p, _ in notes} == {pads[name]},
              f"{name}: expected pitch {pads[name]}")
        check(min(v for _, _, _, v in notes) >= GHOST_VELOCITY,
              f"{name}: a hit is quieter than the audible floor {GHOST_VELOCITY} — the "
              f"sieve selected that step, so it must sound")

        # The rendered rhythm must be the note layer the sieve actually produces.
        layer, periodic = rhythm_from_file(path, step_ticks, note_layer_steps)
        check(periodic, f"{name}: onsets are not periodic on {note_layer_steps} steps")
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

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for stale in glob.glob(os.path.join(OUTPUT_DIR, '*.mid')):
        os.remove(stale)

    base_binaries = {}
    for cfg in INSTRUMENT_CONFIGS:
        binary, _ = build_binary(cfg, base_binaries)
        base_binaries[cfg['name']] = binary

    # The note layer's period is the base sieve's, measured — never declared.
    note_layer_steps = len(base_binaries[INSTRUMENT_CONFIGS[0]['name']])

    print(f"Note layer: {note_layer_steps} steps (derived from the base sieve)\n")
    print("Densities:")
    for cfg in INSTRUMENT_CONFIGS:
        b = base_binaries[cfg['name']]
        print(f"  {cfg['name']}: {b.sum()}/{len(b)} steps ({100 * b.mean():.1f}%)")

    print()
    voices = []
    for cfg in INSTRUMENT_CONFIGS:
        name = cfg['name']
        accent_dict = cfg.get('accent_dict', {})
        binary = base_binaries[name]
        step_ticks = get_step_ticks(cfg)

        span = voice_span(len(binary), accent_dict)
        binary_full = voice_rhythm(cfg, base_binaries, span)
        accent_bins = create_accent_binaries(accent_dict, span)
        if cfg.get('relationship') == 'shift':
            accent_bins = {k: np.roll(v, cfg['shift_amount'])
                           for k, v in accent_bins.items()}

        profile = generate_velocity_profile(accent_bins)
        if accent_dict:
            weights = ", ".join(f"{k} +{v}" for k, v in profile['weights'].items())
            print(f"  {name}: rhythm {len(binary)} steps, accents span {span} "
                  f"({span // len(binary)} iterations) — ghost {profile['ghost']}, {weights}")

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

    note_layer_ticks = note_layer_steps * min(st for _, _, _, st in voices)
    one = shared_meter(list(periods.values()) + [total_ticks], note_layer_ticks)
    if one:
        bar = one[0] * (4 * TICKS_PER_QUARTER_NOTE) // one[1]
        print(f"\n  Shared meter {one[0]}/{one[1]} (bar {bar} ticks) — "
              + ", ".join(f"{n} {p // bar} bars" for n, p in periods.items()))
        meters = {name: one for name in periods}
    else:
        print("\n  No single meter fits every period; using per-voice meters.")
        meters = {}
        for name, _, _, step_ticks in voices:
            m = meter_for_voice(step_ticks, note_layer_steps * step_ticks, periods[name])
            if m is None:
                m = TIME_SIGNATURE
                print(f"  !! {name}: no meter lands on {periods[name]} ticks — "
                      f"falling back to {m[0]}/{m[1]}; a host will pad this clip.")
            meters[name] = m

    print()
    arrangement, merged = [], []
    for name, notes_per_step, velocities, step_ticks in voices:
        events = voice_events(notes_per_step, velocities, step_ticks, periods[name])
        save_tracks([make_track(name, events, periods[name], meters[name])],
                    f"{TITLE}_{name}_prime", periods[name], meters[name])
        repeated = voice_events(notes_per_step, velocities, step_ticks, total_ticks)
        arrangement.append(make_track(name, repeated, total_ticks, meters[name]))
        merged.extend(repeated)

    smallest = min(st for _, _, _, st in voices)
    ensemble_meter = one or meter_for_voice(smallest, note_layer_steps * smallest,
                                            total_ticks) or TIME_SIGNATURE
    print()
    reps = ", ".join(f"{n} x{total_ticks // p}" for n, p in periods.items())
    save_tracks(arrangement, f"{TITLE}_arrangement", total_ticks, ensemble_meter,
                note=f", {len(arrangement)} tracks — {reps}")
    save_tracks([make_track(f"{TITLE} drum rack", merged, total_ticks, ensemble_meter)],
                f"{TITLE}_drumrack", total_ticks, ensemble_meter,
                note=", all voices on one track")

    if not verify(voices, periods, total_ticks, note_layer_steps, base_binaries):
        sys.exit(1)

if __name__ == '__main__':
    main()
