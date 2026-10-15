import os
import glob
import math
import re
import mido
import music21
import numpy as np
from config import *
from transformations import *

def ensure_directory(path):
    os.makedirs(path, exist_ok=True)

def clear_directory(path):
    for file_path in glob.glob(os.path.join(path, '*.mid')):
        os.remove(file_path)

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

    relationship  = config.get('relationship')
    derives_from  = config['derives_from']

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
# Accent voicing (same as dois_three)
# ---------------------------------------------------------------------------

def create_accent_binaries(accent_dict, period):
    binaries = {}
    for label, pattern in accent_dict.items():
        s = music21.sieve.Sieve(pattern)
        s.setZRange(0, period - 1)
        binaries[label] = sieve_to_binary(s)
    return binaries

def generate_velocity_profile(accent_dict, print_profile=False):
    num_levels = len(accent_dict)
    if num_levels == 0:
        return {'gap': 64, 'overlap': 127}

    gap, overlap = 1, 127
    step = (overlap - gap) // (num_levels + 1)
    profile = {'gap': gap, 'overlap': overlap}
    for i, label in enumerate(accent_dict.keys()):
        profile[label] = gap + step * (i + 1)

    if print_profile:
        print("  Velocity profile:")
        for k, v in profile.items():
            print(f"    {k}: {v}")
    return profile

def accent_voicing(binary, accent_binaries, profile, root_note, chord_intervals=None):
    binary = np.asarray(binary)
    n      = len(binary)
    on     = binary.astype(bool)

    label_masks  = {
        label: np.resize(np.asarray(arr, dtype=bool), n)
        for label, arr in accent_binaries.items()
    }
    active_count = sum(label_masks.values(), np.zeros(n, dtype=int))

    velocities = np.zeros(n, dtype=int)
    velocities[on & (active_count == 0)]  = profile['gap']
    velocities[on & (active_count > 1)]   = profile['overlap']
    single_mask = on & (active_count == 1)
    for label, mask in label_masks.items():
        velocities[single_mask & mask] = profile.get(label, profile['gap'])

    notes_per_step = [[] for _ in range(n)]
    active_indices = np.flatnonzero(on)
    if chord_intervals:
        max_count = max(chord_intervals)
        for i in active_indices:
            count = min(int(active_count[i]), max_count) if active_count[i] else 1
            intervals = chord_intervals.get(count, chord_intervals[max_count])
            notes_per_step[i] = [root_note + iv for iv in intervals]
    else:
        for i in active_indices:
            notes_per_step[i] = [root_note]

    return notes_per_step, velocities

# ---------------------------------------------------------------------------
# MIDI rendering
# ---------------------------------------------------------------------------

def get_transformation_func(name):
    if name == 'prime':
        return lambda x: x
    elif name == 'invert':
        return invert_binary
    elif name == 'reverse':
        return reverse_binary
    elif name.startswith('stretch_'):
        m = re.match(r'stretch_(\d+)', name)
        if m:
            factor = int(m.group(1))
            return lambda x: stretch_binary(x, factor)
    raise ValueError(f"Unknown transformation: {name}")

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

def create_midi(notes_per_step, filename, velocities, step_ticks, time_signature):
    mid   = mido.MidiFile(ticks_per_beat=TICKS_PER_QUARTER_NOTE)
    track = mido.MidiTrack()
    mid.tracks.append(track)

    track.append(mido.MetaMessage('track_name', name=filename, time=0))
    num, den = time_signature
    track.append(mido.MetaMessage('time_signature', numerator=num, denominator=den, time=0))

    if not append_note_events(track, notes_per_step, velocities, step_ticks):
        print(f"  Skipping {filename}: no active steps.")
        return

    filepath = os.path.join(OUTPUT_DIR, f"{filename}.mid")
    try:
        mid.save(filepath)
    except OSError as e:
        print(f"Error saving {filename}: {e}")

def create_ensemble_midi(ensemble_tracks, filename):
    if not ensemble_tracks:
        return
    mid = mido.MidiFile(ticks_per_beat=TICKS_PER_QUARTER_NOTE)

    for i, (name, notes_per_step, velocities, step_ticks, time_sig) in enumerate(ensemble_tracks):
        track = mido.MidiTrack()
        track.append(mido.MetaMessage('track_name', name=name, time=0))
        if i == 0:
            num, den = time_sig
            track.append(mido.MetaMessage('time_signature', numerator=num, denominator=den, time=0))
        if append_note_events(track, notes_per_step, velocities, step_ticks):
            mid.tracks.append(track)

    if not mid.tracks:
        return

    filepath = os.path.join(OUTPUT_DIR, f"{filename}.mid")
    try:
        mid.save(filepath)
    except OSError as e:
        print(f"Error saving {filename}: {e}")

def process_instrument(config, base_binary, period, ensemble_tracks):
    name        = config.get('name', 'unnamed')
    accent_dict = config.get('accent_dict', {})
    accent_bins = create_accent_binaries(accent_dict, period)

    if config.get('relationship') == 'shift':
        shift_amount = config.get('shift_amount', 0)
        accent_bins  = {k: np.roll(v, shift_amount) for k, v in accent_bins.items()}

    profile        = generate_velocity_profile(accent_dict, print_profile=bool(accent_dict))
    step_ticks     = get_step_ticks(config)
    time_sig       = generate_time_signature(period, step_ticks)
    root_note      = config.get('root', config.get('note', 64))
    chord_intervals = config.get('chord_intervals')

    for t_name in ['prime'] + config.get('transformations', []):
        try:
            t_func = get_transformation_func(t_name)
        except ValueError as e:
            print(f"  Skipping {t_name} for {name}: {e}")
            continue

        t_binary = t_func(base_binary)
        notes_per_step, velocities = accent_voicing(t_binary, accent_bins, profile, root_note, chord_intervals)
        filename = f"{TITLE}_{name}_{t_name}"
        create_midi(notes_per_step, filename, velocities, step_ticks, time_sig)

        if t_name == 'prime':
            ensemble_tracks.append((name, notes_per_step, velocities, step_ticks, time_sig))

    if config.get('apply_shift', False):
        shift_direction = config.get('shift_direction', 'positive')
        for i in np.nonzero(base_binary)[0]:
            if i == 0:
                continue
            s_values = (
                [int(i), -int(i)] if shift_direction == 'both' else
                [int(i)]          if shift_direction == 'positive' else
                [-int(i)]
            )
            for s in s_values:
                shifted      = np.roll(base_binary, s)
                shifted_bins = {k: np.roll(v, s) for k, v in accent_bins.items()}
                notes_per_step, velocities = accent_voicing(shifted, shifted_bins, profile, root_note, chord_intervals)
                filename = f"{TITLE}_{name}_shift({s:+})"
                create_midi(notes_per_step, filename, velocities, step_ticks, time_sig)

# ---------------------------------------------------------------------------
# Form: window-average downsampling → meso & macro presence maps
# ---------------------------------------------------------------------------

def downsample_binary(binary, z_range, threshold):
    period = len(binary)
    result = np.zeros(z_range, dtype=int)
    for i in range(z_range):
        lo = int(i * period / z_range)
        hi = int((i + 1) * period / z_range)
        if hi > lo and binary[lo:hi].mean() >= threshold:
            result[i] = 1
    return result

def build_all_presences(instrument_configs, base_binaries, z_range):
    presences = {}
    for config in instrument_configs:
        name      = config['name']
        threshold = config.get('presence_threshold', PRESENCE_THRESHOLD)
        presences[name] = downsample_binary(base_binaries[name], z_range, threshold)
    return presences

# ---------------------------------------------------------------------------
# Arrangement
# ---------------------------------------------------------------------------

def print_form_plan(meso_presences, macro_presences, names):
    print(f"\nForm plan  ({NUM_MOVEMENTS} mov × {NUM_SECTIONS_PER_MOVEMENT} sec = {NUM_MOVEMENTS * NUM_SECTIONS_PER_MOVEMENT} = sieve period)")
    print(f"  {'Instrument':12s}  {'Macro movements':20s}  {'Meso sections':20s}  Global")
    for name in names:
        macro  = np.flatnonzero(macro_presences[name]).tolist()
        meso   = np.flatnonzero(meso_presences[name]).tolist()
        global_count = sum(
            1 for m in range(NUM_MOVEMENTS) if macro_presences[name][m]
            for s in range(NUM_SECTIONS_PER_MOVEMENT) if meso_presences[name][s]
        )
        pct = 100 * global_count / (NUM_MOVEMENTS * NUM_SECTIONS_PER_MOVEMENT)
        print(f"  {name:12s}  {str(macro):20s}  {str(meso):20s}  {global_count:2d}/40  ({pct:.0f}%)")
    print()

def create_arrangement(ensemble_tracks, meso_presences, macro_presences, filename):
    if not ensemble_tracks:
        return

    cycle_lengths      = [len(velocities) * step_ticks
                          for (_, _, velocities, step_ticks, _) in ensemble_tracks]
    base_section_ticks = math.lcm(*cycle_lengths)
    section_ticks      = base_section_ticks * SECTION_REPETITIONS

    ON, OFF = 1, 0
    mid = mido.MidiFile(ticks_per_beat=TICKS_PER_QUARTER_NOTE)

    for name, notes_per_step, velocities, step_ticks, time_sig in ensemble_tracks:
        macro_bin = macro_presences.get(name, np.zeros(NUM_MOVEMENTS, dtype=int))
        meso_bin  = meso_presences.get(name,  np.zeros(NUM_SECTIONS_PER_MOVEMENT, dtype=int))

        cycle_ticks = len(velocities) * step_ticks
        reps        = section_ticks // cycle_ticks
        active      = np.flatnonzero(velocities)
        if active.size == 0:
            continue

        for m in range(NUM_MOVEMENTS):
            if not macro_bin[m]:
                continue

            events = []
            mov_start = m * NUM_SECTIONS_PER_MOVEMENT * section_ticks
            for s in range(NUM_SECTIONS_PER_MOVEMENT):
                if not meso_bin[s]:
                    continue
                sec_start = mov_start + s * section_ticks
                for rep in range(reps):
                    rep_start = sec_start + rep * cycle_ticks
                    for idx in active:
                        on_tick  = rep_start + int(idx) * step_ticks
                        off_tick = on_tick + step_ticks
                        velocity = int(velocities[idx])
                        for pitch in notes_per_step[idx]:
                            events.append((on_tick,  ON,  int(pitch), velocity))
                            events.append((off_tick, OFF, int(pitch), 0))

            if not events:
                continue

            events.sort(key=lambda e: (e[0], e[1]))

            track_name = f"{TITLE}_{name}_mov{m}"
            track = mido.MidiTrack()
            track.append(mido.MetaMessage('track_name', name=track_name, time=0))
            if not mid.tracks:
                num, den = time_sig
                track.append(mido.MetaMessage('time_signature', numerator=num, denominator=den, time=0))

            prev = 0
            for abs_tick, kind, pitch, vel in events:
                delta = abs_tick - prev
                msg   = 'note_on' if kind == ON else 'note_off'
                track.append(mido.Message(msg, note=pitch, velocity=vel, time=delta))
                prev = abs_tick

            mid.tracks.append(track)

    if not mid.tracks:
        print(f"Skipping {filename}: nothing to write.")
        return

    total_ticks = NUM_MOVEMENTS * NUM_SECTIONS_PER_MOVEMENT * section_ticks
    total_qn    = total_ticks / TICKS_PER_QUARTER_NOTE
    print(f"Arrangement: {NUM_MOVEMENTS} mov × {NUM_SECTIONS_PER_MOVEMENT} sec × "
          f"{SECTION_REPETITIONS} reps × {base_section_ticks} ticks "
          f"= {total_ticks} ticks ({total_qn:.0f} QN ≈ {total_qn / 120:.1f} min at 120 BPM)")

    filepath = os.path.join(OUTPUT_DIR, f"{filename}.mid")
    try:
        mid.save(filepath)
    except OSError as e:
        print(f"Error saving {filename}: {e}")

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ensure_directory(OUTPUT_DIR)
    clear_directory(OUTPUT_DIR)

    # Pass 1 — build all micro binaries (dependency order matters).
    base_binaries = {}
    for config in INSTRUMENT_CONFIGS:
        binary, period = build_binary(config, base_binaries)
        base_binaries[config['name']] = binary

    print("Micro binary densities:")
    for config in INSTRUMENT_CONFIGS:
        name   = config['name']
        binary = base_binaries[name]
        print(f"  {name}: {binary.sum()}/{len(binary)} steps ({100 * binary.mean():.1f}%)")

    # Pass 2 — render per-clip library (same as dois_three).
    print()
    ensemble_tracks = []
    for config in INSTRUMENT_CONFIGS:
        process_instrument(config, base_binaries[config['name']], len(base_binaries[config['name']]), ensemble_tracks)

    create_ensemble_midi(ensemble_tracks, filename=f"{TITLE}_ensemble_prime")

    # Pass 3 — meso presence: downsample micro binaries to NUM_SECTIONS_PER_MOVEMENT.
    meso_presences = build_all_presences(INSTRUMENT_CONFIGS, base_binaries, NUM_SECTIONS_PER_MOVEMENT)

    # Pass 4 — macro presence: downsample micro binaries to NUM_MOVEMENTS.
    macro_presences = build_all_presences(INSTRUMENT_CONFIGS, base_binaries, NUM_MOVEMENTS)

    names = [config['name'] for config in INSTRUMENT_CONFIGS]
    print_form_plan(meso_presences, macro_presences, names)

    # Pass 5 — render the arrangement.
    create_arrangement(ensemble_tracks, meso_presences, macro_presences,
                       filename=f"{TITLE}_arrangement")

if __name__ == '__main__':
    main()
