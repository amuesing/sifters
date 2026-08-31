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

def append_header(track, name):
    """Name, meter and tempo — written identically at the head of every track."""
    track.append(mido.MetaMessage('track_name', name=name, time=0))
    num, den = TIME_SIGNATURE
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

def generate_velocity_profile(accent_dict):
    if not accent_dict:
        return {'gap': 64, 'overlap': 127}
    gap, overlap = 1, 127
    step = (overlap - gap) // (len(accent_dict) + 1)
    profile = {'gap': gap, 'overlap': overlap}
    for i, label in enumerate(accent_dict.keys()):
        profile[label] = gap + step * (i + 1)
    return profile

def accent_voicing(binary, accent_binaries, profile, root_note):
    binary = np.asarray(binary)
    n = len(binary)
    on = binary.astype(bool)

    label_masks = {
        label: np.resize(np.asarray(arr, dtype=bool), n)
        for label, arr in accent_binaries.items()
    }
    active_count = sum(label_masks.values(), np.zeros(n, dtype=int))

    velocities = np.zeros(n, dtype=int)
    velocities[on & (active_count == 0)] = profile['gap']
    velocities[on & (active_count > 1)]  = profile['overlap']
    single_mask = on & (active_count == 1)
    for label, mask in label_masks.items():
        velocities[single_mask & mask] = profile.get(label, profile['gap'])

    notes_per_step = [[] for _ in range(n)]
    for i in np.flatnonzero(on):
        notes_per_step[i] = [root_note]

    return notes_per_step, velocities

# ---------------------------------------------------------------------------
# MIDI rendering
# ---------------------------------------------------------------------------
# Duration states periodicity — see "Governing Principle" in CONTEXT.md. A voice appears
# as EXACTLY ONE period of its sieve, at its own basic unit, in every file it appears in:
# the per-voice file, the arrangement and the drum rack all carry the same single statement.
# Voices on different basic units therefore have different durations, which is correct and
# not a defect. Keeping them identical across files is what makes the per-voice files usable
# as a reference to check the ensemble files against.

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

def make_track(name, events, total_ticks):
    """One MIDI track: shared header, events in delta time, end_of_track on the boundary."""
    track = mido.MidiTrack()
    append_header(track, name)

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

def save_tracks(tracks, filename, total_ticks, note=''):
    mid = mido.MidiFile(ticks_per_beat=TICKS_PER_QUARTER_NOTE)
    mid.tracks.extend(tracks)

    filepath = os.path.join(OUTPUT_DIR, f"{filename}.mid")
    try:
        mid.save(filepath)
        bars = total_ticks / (TICKS_PER_QUARTER_NOTE * 4)
        num, den = TIME_SIGNATURE
        print(f"  Saved: {filename}.mid  ({total_ticks} ticks = {bars:g} bars "
              f"of {num}/{den}{note})")
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

        profile = generate_velocity_profile(accent_dict)
        if accent_dict:
            print(f"  {name}: rhythm {rhythm} steps, accents span {span} "
                  f"({span // rhythm} iterations of the note layer) — " +
                  ", ".join(f"{k}={v}" for k, v in profile.items()))

        notes_per_step, velocities = accent_voicing(binary_full, accent_bins, profile, root_note)
        voices.append((name, notes_per_step, velocities, step_ticks))

    # A voice's period is its own; the ensemble's period is the LCM of those.
    periods     = {name: len(vel) * st for name, _, vel, st in voices}
    total_ticks = math.lcm(*periods.values())

    print(f"\n  Voice periods (one full statement at that voice's basic unit):")
    for name, _, velocities, step_ticks in voices:
        print(f"    {name}: {len(velocities)} steps x {step_ticks} ticks = {periods[name]} ticks"
              f"  ({periods[name] / (TICKS_PER_QUARTER_NOTE * 4):g} bars)")
    print(f"  (For reference only — every voice is stated ONCE, never repeated to fill a")
    print(f"   common length. All voices would realign after {total_ticks} ticks "
          f"= {total_ticks / (TICKS_PER_QUARTER_NOTE * 4):g} bars: "
          f"{', '.join(f'{n} x{total_ticks // c}' for n, c in periods.items())}.)")
    print()

    # Build each voice's single statement once, then use that same statement everywhere.
    arrangement, merged = [], []
    for name, notes_per_step, velocities, step_ticks in voices:
        period_ticks = periods[name]
        events = voice_events(notes_per_step, velocities, step_ticks, period_ticks)

        save_tracks([make_track(name, events, period_ticks)],
                    f"{TITLE}_{name}_prime", period_ticks)
        arrangement.append(make_track(name, events, period_ticks))
        merged.extend(events)

    # The ensemble files hold the same statements, so each voice's track and pad is
    # identical to its own file. The file is as long as the longest voice; tracks keep
    # their own end_of_track, so no voice is padded out to match another.
    longest = max(periods.values())
    print()
    save_tracks(arrangement, f"{TITLE}_arrangement", longest,
                note=f", {len(arrangement)} tracks, each one period")
    save_tracks([make_track(f"{TITLE} drum rack", merged, longest)],
                f"{TITLE}_drumrack", longest, note=", all voices on one track, one period each")

if __name__ == '__main__':
    main()
