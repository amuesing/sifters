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

def create_accent_binaries(accent_dict, period):
    binaries = {}
    for label, pattern in accent_dict.items():
        s = music21.sieve.Sieve(pattern)
        s.setZRange(0, period - 1)
        binaries[label] = sieve_to_binary(s)
    return binaries

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
# Every file spans the same length: the LCM of all voice cycles. Each voice therefore
# repeats a whole number of times and they all land on beat 1 together at the end, so
# any combination of these files can be looped side by side without drifting.

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
        period      = len(binary)
        step_ticks  = get_step_ticks(cfg)

        accent_bins = create_accent_binaries(accent_dict, period)
        if cfg.get('relationship') == 'shift':
            shift_amount = cfg.get('shift_amount', 0)
            accent_bins  = {k: np.roll(v, shift_amount) for k, v in accent_bins.items()}

        profile = generate_velocity_profile(accent_dict)
        if accent_dict:
            print(f"  {name} velocity profile: " +
                  ", ".join(f"{k}={v}" for k, v in profile.items()))

        notes_per_step, velocities = accent_voicing(binary, accent_bins, profile, root_note)
        voices.append((name, notes_per_step, velocities, step_ticks))

    # One span for every file, so no output ever cuts a voice mid-cycle.
    total_ticks = math.lcm(*(len(vel) * st for _, _, vel, st in voices))
    print(f"\n  Every file spans {total_ticks} ticks "
          f"({total_ticks / (TICKS_PER_QUARTER_NOTE * 4):g} bars) — the LCM of the voice cycles:")
    for name, _, velocities, step_ticks in voices:
        cycle = len(velocities) * step_ticks
        print(f"    {name}: cycle {cycle} x {total_ticks // cycle} reps = {total_ticks}")
    print()

    # One file per voice, each covering the full span.
    arrangement, merged = [], []
    for name, notes_per_step, velocities, step_ticks in voices:
        events = voice_events(notes_per_step, velocities, step_ticks, total_ticks)
        save_tracks([make_track(name, events, total_ticks)],
                    f"{TITLE}_{name}_prime", total_ticks)
        arrangement.append(make_track(name, events, total_ticks))
        merged.extend(events)

    print()
    save_tracks(arrangement, f"{TITLE}_arrangement", total_ticks,
                note=f", {len(arrangement)} tracks")
    save_tracks([make_track(f"{TITLE} drum rack", merged, total_ticks)],
                f"{TITLE}_drumrack", total_ticks, note=", all voices on one track")

if __name__ == '__main__':
    main()
