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

def generate_time_signature(period, step_ticks):
    if period > 255:
        raise ValueError(f"Period {period} exceeds 255.")
    denominator = STEP_TICKS_TO_DENOMINATOR.get(step_ticks, 16)
    if step_ticks == 60:
        return period // 2, denominator
    return period, denominator

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

def append_note_events(track, notes_per_step, velocities, step_ticks):
    active_indices = np.flatnonzero(velocities)
    if active_indices.size == 0:
        return False

    rest_steps = np.empty(active_indices.size, dtype=np.int64)
    rest_steps[0] = active_indices[0]
    rest_steps[1:] = np.diff(active_indices) - 1
    note_on_times = rest_steps * step_ticks

    for idx, rest_ticks in zip(active_indices, note_on_times):
        pitches  = notes_per_step[idx]
        velocity = int(velocities[idx])
        for j, pitch in enumerate(pitches):
            track.append(mido.Message('note_on',  note=int(pitch), velocity=velocity,
                                      time=int(rest_ticks) if j == 0 else 0))
        for j, pitch in enumerate(pitches):
            track.append(mido.Message('note_off', note=int(pitch), velocity=0,
                                      time=step_ticks if j == 0 else 0))
    return True

def save_midi(tracks_data, filename):
    mid = mido.MidiFile(ticks_per_beat=TICKS_PER_QUARTER_NOTE)
    for name, notes_per_step, velocities, step_ticks, time_sig in tracks_data:
        track = mido.MidiTrack()
        track.append(mido.MetaMessage('track_name', name=name, time=0))
        num, den = time_sig
        track.append(mido.MetaMessage('time_signature', numerator=num, denominator=den, time=0))

        cycle_ticks = len(velocities) * step_ticks
        active_indices = np.flatnonzero(velocities)

        if active_indices.size > 0:
            append_note_events(track, notes_per_step, velocities, step_ticks)
            last_note_off = (int(active_indices[-1]) + 1) * step_ticks
        else:
            last_note_off = 0

        # Pad to the true cycle boundary so Ableton reads the correct clip length.
        remaining = cycle_ticks - last_note_off
        track.append(mido.MetaMessage('end_of_track', time=remaining))
        mid.tracks.append(track)

    if not mid.tracks:
        return
    filepath = os.path.join(OUTPUT_DIR, f"{filename}.mid")
    try:
        mid.save(filepath)
        print(f"  Saved: {filename}.mid")
    except OSError as e:
        print(f"  Error saving {filename}: {e}")

def save_ensemble_loop(tracks_data, filename):
    """Write all voices out for exactly one LCM cycle so every rhythm realigns at the end."""
    cycle_lengths = [len(velocities) * step_ticks
                     for (_, _, velocities, step_ticks, _) in tracks_data]
    total_ticks = math.lcm(*cycle_lengths)

    mid = mido.MidiFile(ticks_per_beat=TICKS_PER_QUARTER_NOTE)

    for name, notes_per_step, velocities, step_ticks, time_sig in tracks_data:
        active = np.flatnonzero(velocities)
        if active.size == 0:
            continue

        cycle_ticks = len(velocities) * step_ticks
        reps = total_ticks // cycle_ticks

        events = []
        for rep in range(reps):
            rep_start = rep * cycle_ticks
            for idx in active:
                on_tick  = rep_start + int(idx) * step_ticks
                off_tick = on_tick + step_ticks
                velocity = int(velocities[idx])
                for pitch in notes_per_step[idx]:
                    events.append((on_tick,  1, int(pitch), velocity))
                    events.append((off_tick, 0, int(pitch), 0))

        events.sort(key=lambda e: (e[0], e[1]))

        track = mido.MidiTrack()
        track.append(mido.MetaMessage('track_name', name=name, time=0))
        num, den = time_sig
        track.append(mido.MetaMessage('time_signature', numerator=num, denominator=den, time=0))

        prev = 0
        for abs_tick, kind, pitch, vel in events:
            delta = abs_tick - prev
            track.append(mido.Message(
                'note_on' if kind == 1 else 'note_off',
                note=pitch, velocity=vel, time=delta))
            prev = abs_tick

        track.append(mido.MetaMessage('end_of_track', time=total_ticks - prev))
        mid.tracks.append(track)

    if not mid.tracks:
        return

    filepath = os.path.join(OUTPUT_DIR, f"{filename}.mid")
    try:
        mid.save(filepath)
        total_qn = total_ticks / TICKS_PER_QUARTER_NOTE
        print(f"  Saved: {filename}.mid  "
              f"({total_ticks} ticks = {total_qn:.0f} QN, "
              f"cycle lengths: {cycle_lengths}, reps: "
              f"{[total_ticks // c for c in cycle_lengths]})")
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

    # Render one prime clip per instrument + collect for ensemble.
    print()
    ensemble_tracks = []
    for cfg in INSTRUMENT_CONFIGS:
        name        = cfg['name']
        accent_dict = cfg.get('accent_dict', {})
        root_note   = cfg.get('root', 60)
        binary      = base_binaries[name]
        period      = len(binary)
        step_ticks  = get_step_ticks(cfg)
        time_sig    = generate_time_signature(period, step_ticks)

        accent_bins = create_accent_binaries(accent_dict, period)
        if cfg.get('relationship') == 'shift':
            shift_amount = cfg.get('shift_amount', 0)
            accent_bins  = {k: np.roll(v, shift_amount) for k, v in accent_bins.items()}

        profile = generate_velocity_profile(accent_dict)
        if accent_dict:
            print(f"  {name} velocity profile: " +
                  ", ".join(f"{k}={v}" for k, v in profile.items()))

        notes_per_step, velocities = accent_voicing(binary, accent_bins, profile, root_note)
        filename = f"{TITLE}_{name}_prime"
        save_midi([(name, notes_per_step, velocities, step_ticks, time_sig)], filename)
        ensemble_tracks.append((name, notes_per_step, velocities, step_ticks, time_sig))

    # Arrangement: one full LCM cycle — A/B/C × 4, D × 3, all realign at the end.
    print()
    save_ensemble_loop(ensemble_tracks, f"{TITLE}_arrangement")

if __name__ == '__main__':
    main()
