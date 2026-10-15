import os
import glob
import math
import mido
import music21
import numpy as np
from config import *
from transformations import *

def ensure_directory(path):
    os.makedirs(path, exist_ok=True)

def clear_directory(path):
    for f in glob.glob(os.path.join(path, '*.mid')):
        os.remove(f)

def sieve_to_binary(sieve_obj):
    return np.array(sieve_obj.segment(segmentFormat='binary'))

def get_step_ticks(config):
    if 'step_ticks' in config:
        return config['step_ticks']
    duration = config.get('duration', 'Quarter Note')
    return int(TICKS_PER_QUARTER_NOTE * DURATION_MULTIPLIER_KEY.get(duration, 0.25))

def meter_for_voice(step_ticks, note_layer_ticks, period_ticks):
    """A meter in which this voice's clip ends exactly on a bar line.

    Preference 1 — the beat IS the voice's basic unit, and the bar is one pass of the
    note layer. A sixteenth grid (120 ticks) gives 4*TPQ/120 = 16, so 40 steps is 40/16:
    one bar per statement of the rhythm, which is the most legible result.

    Preference 2 — for a grid that is not a power-of-two subdivision, no meter can have
    it as the beat (a triplet gives 4*TPQ/160 = 12, not a valid denominator). Fall back
    to any meter whose BAR equals the voice's full period. D's 120 x 160 = 19200 ticks is
    exactly 40 quarter notes, so 40/4 works: the beat is no longer D's own unit, but the
    bar still lands precisely on the period, which is what stops a host padding the clip.
    Denominators are tried in order of how conventional the beat is.

    Returns None only if neither is possible.
    """
    beat = (4 * TICKS_PER_QUARTER_NOTE) / step_ticks
    if beat == int(beat) and not (int(beat) & (int(beat) - 1)):
        n = note_layer_ticks // step_ticks
        if 1 <= n <= MAX_METER_NUMERATOR:
            return int(n), int(beat)

    for den in (4, 8, 16, 2, 32, 1, 64):
        beat = (4 * TICKS_PER_QUARTER_NOTE) / den
        if beat != int(beat):
            continue
        beat = int(beat)
        if period_ticks % beat == 0:
            n = period_ticks // beat
            if 1 <= n <= MAX_METER_NUMERATOR:
                return n, den
    return None

def shared_meter(lengths, units):
    """One meter for every voice, when one exists.

    The natural bar is one pass of the note layer at the finest basic unit
    (40 x 120 = 4800 ticks), which is the project's original 40/16. It can be shared
    only if EVERY length given is a whole number of those bars — otherwise some clip
    would not end on a bar line and the host would pad it.

    This became possible only once D gained its accent layer: D's period was 6400,
    which 4800 does not divide, so no shared meter existed. At 19200 it does (4 bars).
    """
    bar = NOTE_LAYER_STEPS * min(units)
    if any(length % bar for length in lengths):
        return None
    for den in (16, 8, 4, 32, 2, 64, 1):
        beat = (4 * TICKS_PER_QUARTER_NOTE) / den
        if beat != int(beat):
            continue
        beat = int(beat)
        if bar % beat == 0:
            n = bar // beat
            if 1 <= n <= MAX_METER_NUMERATOR:
                return n, den
    return None

def append_header(track, name, meter):
    """Name, meter and tempo at the head of a track."""
    track.append(mido.MetaMessage('track_name', name=name, time=0))
    num, den = meter
    track.append(mido.MetaMessage('time_signature', numerator=num, denominator=den, time=0))
    track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(TEMPO_BPM), time=0))

# ---------------------------------------------------------------------------
# Binary construction
# ---------------------------------------------------------------------------

def build_binary(config, base_binaries):
    if 'sieve' in config:
        sieve = music21.sieve.Sieve(config['sieve'])
        period = sieve.period()
        sieve.setZRange(0, period - 1)
        return sieve_to_binary(sieve), period

    relationship = config.get('relationship')
    derives_from = config['derives_from']

    if relationship == 'complement':
        src = base_binaries[derives_from]
        return 1 - src, len(src)

    elif relationship == 'shift':
        src = base_binaries[derives_from]
        return np.roll(src, config['shift_amount']), len(src)

    elif relationship == 'intersection':
        sources = [base_binaries[n] for n in derives_from]
        result = sources[0].copy()
        for s in sources[1:]:
            result = result & s
        return result, len(result)

    raise ValueError(f"Unknown relationship: {relationship}")

# ---------------------------------------------------------------------------
# Accent voicing
# ---------------------------------------------------------------------------

def create_accent_binaries(accent_dict, span):
    """Accent masks evaluated across the voice's FULL span, not just one rhythm period.

    Evaluating them over the rhythm period alone would restart every accent at each
    repeat; carrying them across the span is what lets them land differently on each
    pass of the note layer.
    """
    binaries = {}
    for label, pattern in accent_dict.items():
        s = music21.sieve.Sieve(pattern)
        s.setZRange(0, span - 1)
        binaries[label] = sieve_to_binary(s)
    return binaries

def voice_span(rhythm_period, accent_dict):
    """Steps in one full statement of a voice: LCM of the rhythm and accent periods.

    The note layer repeats every `rhythm_period` steps, but an accent sieve whose
    modulus does not divide that lands differently on each pass. The voice has not
    stated itself completely until the two agree again. For the psappha voices the
    rhythm is 40 steps (moduli 8, 5) and the accents add modulus 3, so a full
    statement is LCM(40, 3) = 120 steps — the accent layer spans three iterations
    of the note layer, re-accenting the same figure each time.
    """
    periods = [rhythm_period]
    for pattern in accent_dict.values():
        periods.append(music21.sieve.Sieve(pattern).period())
    return math.lcm(*periods)

def generate_velocity_profile(accent_binaries):
    """Velocity is a weighted SUM of the accents firing — not a count of them.

    An accent's weight is how rarely it fires: weight is proportional to (1 - density).
    An accent covering two thirds of the steps carries almost no information and should
    barely lift a note; a sparse one is genuinely an accent and should lift it a lot. An
    accent that fired on every step would earn weight 0, which is correct — it says
    nothing.

    Why not count overlaps, as this did before: counting throws away WHICH accents fired.
    Four accents have 16 combinations but only 5 counts, and because the sieves are dense
    those counts bunch around their mean — 72% of voice A's notes sat on count 2 or 3, an
    18-point spread inside a 127-point range. It also made a sparse accent inaudible
    unless it fired alone, which for span32 never once happened in 180 notes. Under a
    weighted sum every accent is audible every time it fires, and adding a layer widens
    the palette instead of narrowing it.
    """
    GHOST, FULL = 1, 127
    if not accent_binaries:
        return {'ghost': 64, 'weights': {}}

    rarity = {label: 1.0 - float(np.mean(arr)) for label, arr in accent_binaries.items()}
    total  = sum(rarity.values()) or 1.0
    budget = FULL - GHOST
    weights = {label: int(round(budget * r / total)) for label, r in rarity.items()}

    # Rounding can miss the budget; settle the difference on the heaviest accent so all
    # four firing together still reaches exactly FULL.
    drift = budget - sum(weights.values())
    if drift:
        weights[max(weights, key=weights.get)] += drift
    return {'ghost': GHOST, 'weights': weights}

def accent_voicing(binary, accent_binaries, profile, root_note):
    binary = np.asarray(binary)
    n = len(binary)
    on = binary.astype(bool)

    label_masks = {
        label: np.resize(np.asarray(arr, dtype=bool), n)
        for label, arr in accent_binaries.items()
    }

    # Ghost floor, plus each firing accent's own weight — so which accents are
    # present matters, not merely how many.
    level = np.full(n, profile['ghost'], dtype=int)
    for label, weight in profile['weights'].items():
        level += weight * label_masks[label].astype(int)

    velocities = np.zeros(n, dtype=int)
    velocities[on] = np.clip(level[on], 1, 127)

    notes_per_step = [[] for _ in range(n)]
    for i in np.flatnonzero(on):
        notes_per_step[i] = [root_note]

    return notes_per_step, velocities

# ---------------------------------------------------------------------------
# MIDI rendering
# ---------------------------------------------------------------------------
# Duration states periodicity — see "Governing Principle" in CONTEXT.md.
#
# A per-voice file is EXACTLY ONE period of that voice's sieve, at its own basic unit.
# Voices on different units, or with different accent spans, therefore have different
# lengths — correct, not a defect.
#
# The ensemble files repeat each voice a WHOLE number of its own periods, enough for
# every voice to finish together: the LCM of the voice periods. A voice's internal
# period is never altered to fit — it simply recurs. So one cycle inside an ensemble
# file is identical to that voice's own file, which is what makes the per-voice files
# usable as a reference for checking the ensemble.

def voice_events(notes_per_step, velocities, step_ticks, total_ticks):
    """Absolute-time events for one voice, repeated to fill total_ticks.

    Each event is (tick, kind, pitch, velocity); kind 1 = note_on, 0 = note_off.
    """
    active = np.flatnonzero(velocities)
    if active.size == 0:
        return []

    cycle_ticks = len(velocities) * step_ticks
    events = []
    for rep in range(total_ticks // cycle_ticks):
        rep_start = rep * cycle_ticks
        for idx in active:
            on_tick  = rep_start + int(idx) * step_ticks
            velocity = int(velocities[idx])
            for pitch in notes_per_step[idx]:
                events.append((on_tick,              1, int(pitch), velocity))
                events.append((on_tick + step_ticks, 0, int(pitch), 0))
    return events

def make_track(name, events, total_ticks, meter):
    """One MIDI track: header, events in delta time, end_of_track on the boundary."""
    track = mido.MidiTrack()
    append_header(track, name, meter)

    # note_off (kind 0) sorts ahead of note_on at the same tick, so a pitch that
    # retriggers on consecutive steps releases before it strikes again.
    prev = 0
    for abs_tick, kind, pitch, vel in sorted(events, key=lambda e: (e[0], e[1])):
        track.append(mido.Message('note_on' if kind == 1 else 'note_off',
                                  note=pitch, velocity=vel, time=abs_tick - prev))
        prev = abs_tick

    # Pad to the true boundary so the host reads the correct clip length rather than
    # stopping at the last note.
    track.append(mido.MetaMessage('end_of_track', time=total_ticks - prev))
    return track

def save_tracks(tracks, filename, total_ticks, meter, note=''):
    mid = mido.MidiFile(ticks_per_beat=TICKS_PER_QUARTER_NOTE)
    mid.tracks.extend(tracks)

    filepath = os.path.join(OUTPUT_DIR, f"{filename}.mid")
    num, den = meter
    bar_ticks = num * (4 * TICKS_PER_QUARTER_NOTE) // den
    bars = total_ticks / bar_ticks
    exact = "" if total_ticks % bar_ticks == 0 else "  <-- NOT whole bars, host will pad"
    try:
        mid.save(filepath)
        print(f"  Saved: {filename}.mid  ({total_ticks} ticks = {bars:g} bars "
              f"of {num}/{den}{note}){exact}")
    except OSError as e:
        print(f"  Error saving {filename}: {e}")

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ensure_directory(OUTPUT_DIR)
    clear_directory(OUTPUT_DIR)

    # Build all binaries in dependency order.
    base_binaries = {}
    for cfg in INSTRUMENT_CONFIGS:
        binary, period = build_binary(cfg, base_binaries)
        base_binaries[cfg['name']] = binary

    print("Densities:")
    for cfg in INSTRUMENT_CONFIGS:
        name = cfg['name']
        b = base_binaries[name]
        print(f"  {name}: {b.sum()}/{len(b)} steps ({100 * b.mean():.1f}%)")

    # Build every voice's note data first — the shared file length depends on all of them.
    print()
    voices = []
    for cfg in INSTRUMENT_CONFIGS:
        name        = cfg['name']
        accent_dict = cfg.get('accent_dict', {})
        root_note   = cfg['root']
        binary      = base_binaries[name]
        rhythm      = len(binary)
        step_ticks  = get_step_ticks(cfg)

        # One statement = rhythm and accents realigned. Tile the note layer across it.
        span         = voice_span(rhythm, accent_dict)
        binary_full  = np.resize(binary, span)
        accent_bins  = create_accent_binaries(accent_dict, span)
        if cfg.get('relationship') == 'shift':
            shift_amount = cfg.get('shift_amount', 0)
            accent_bins  = {k: np.roll(v, shift_amount) for k, v in accent_bins.items()}

        profile = generate_velocity_profile(accent_bins)
        if accent_dict:
            w = ", ".join(f"{k} +{v}" for k, v in profile['weights'].items())
            print(f"  {name}: rhythm {rhythm} steps, accents span {span} "
                  f"({span // rhythm} iterations) — ghost {profile['ghost']}, {w}")

        notes_per_step, velocities = accent_voicing(binary_full, accent_bins, profile, root_note)
        voices.append((name, notes_per_step, velocities, step_ticks))

    # A voice's period is its own; the ensemble's period is the LCM of those.
    periods     = {name: len(vel) * st for name, _, vel, st in voices}
    total_ticks = math.lcm(*periods.values())

    print(f"\n  Voice periods (one full statement at that voice's basic unit):")
    for name, _, velocities, step_ticks in voices:
        print(f"    {name}: {len(velocities)} steps x {step_ticks} ticks = {periods[name]} ticks"
              f"  ({periods[name] / (TICKS_PER_QUARTER_NOTE * 4):g} bars)")
    print(f"  Ensemble length {total_ticks} ticks "
          f"({total_ticks / (TICKS_PER_QUARTER_NOTE * 4):g} bars) — LCM of the voice periods, "
          f"so every voice completes whole cycles and all end together:")
    for name, _, _, _ in voices:
        print(f"    {name}: {periods[name]} x {total_ticks // periods[name]} = {total_ticks}")
    print()

    # Per-voice file: one period. Ensemble: that same period recurring a whole number
    # of times, so cycle k of the ensemble equals the per-voice file exactly.
    # Prefer ONE meter for everything: every clip still ends on a bar line, and the
    # voices agree, which is easier to work with in a host. Fall back to per-voice
    # meters only if no single meter fits every length.
    units    = [st for _, _, _, st in voices]
    lengths  = list(periods.values()) + [total_ticks]
    one      = shared_meter(lengths, units)

    if one:
        bar = one[0] * (4 * TICKS_PER_QUARTER_NOTE) // one[1]
        print(f"\n  Shared meter {one[0]}/{one[1]} (bar = {bar} ticks) — every voice's "
              f"period is a whole number of bars: "
              + ", ".join(f"{n} {p // bar}" for n, p in periods.items()))
        meters = {name: one for name in periods}
    else:
        print(f"\n  No single meter fits every period; using per-voice meters.")
        meters = {}
        for name, _, _, step_ticks in voices:
            m = meter_for_voice(step_ticks, NOTE_LAYER_STEPS * step_ticks, periods[name])
            if m is None:
                m = TIME_SIGNATURE
                print(f"  !! {name}: no meter puts a bar line on {periods[name]} ticks — "
                      f"falling back to {m[0]}/{m[1]}; a host will pad this clip.")
            meters[name] = m

    arrangement, merged = [], []
    for name, notes_per_step, velocities, step_ticks in voices:
        events = voice_events(notes_per_step, velocities, step_ticks, periods[name])
        save_tracks([make_track(name, events, periods[name], meters[name])],
                    f"{TITLE}_{name}_prime", periods[name], meters[name])

        repeated = voice_events(notes_per_step, velocities, step_ticks, total_ticks)
        arrangement.append(make_track(name, repeated, total_ticks, meters[name]))
        merged.extend(repeated)

    # The ensemble runs on the majority grid, in which its length is whole bars.
    smallest = min(st for _, _, _, st in voices)
    ens = one or meter_for_voice(smallest, NOTE_LAYER_STEPS * smallest,
                                 total_ticks) or TIME_SIGNATURE
    print()
    reps = ", ".join(f"{n} x{total_ticks // c}" for n, c in periods.items())
    save_tracks(arrangement, f"{TITLE}_arrangement", total_ticks, ens,
                note=f", {len(arrangement)} tracks — {reps}")
    save_tracks([make_track(f"{TITLE} drum rack", merged, total_ticks, ens)],
                f"{TITLE}_drumrack", total_ticks, ens, note=", all voices on one track")

if __name__ == '__main__':
    main()
