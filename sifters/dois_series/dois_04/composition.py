import os
import glob
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

def get_duration_multiplier(duration_name):
    return DURATION_MULTIPLIER_KEY.get(duration_name, 0.25)

def get_step_ticks(config):
    if 'step_ticks' in config:
        return config['step_ticks']
    duration = config.get('duration', 'Quarter Note')
    return int(TICKS_PER_QUARTER_NOTE * get_duration_multiplier(duration))

def generate_time_signature(period, step_ticks):
    if period > 255:
        raise ValueError(f"The period {period} exceeds 255.")
    denominator = STEP_TICKS_TO_DENOMINATOR.get(step_ticks, 16)
    if step_ticks == 60:  # thirty-second note halves the numerator
        return period // 2, denominator
    return period, denominator

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

    gap = 1
    overlap = 127
    step = (overlap - gap) // (num_levels + 1)

    profile = {'gap': gap, 'overlap': overlap}
    for i, label in enumerate(accent_dict.keys()):
        profile[label] = gap + step * (i + 1)

    if print_profile:
        print("Generated velocity profile:")
        for k, v in profile.items():
            print(f"  {k}: {v}")

    return profile

def accent_voicing(binary, accent_binaries, profile, root_note, chord_intervals=None):
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
    velocities[on & (active_count > 1)] = profile['overlap']

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
            notes_per_step[i] = [root_note + interval for interval in intervals]
    else:
        for i in active_indices:
            notes_per_step[i] = [root_note]

    return notes_per_step, velocities

def append_note_events(track, notes_per_step, velocities, step_ticks):
    active_indices = np.flatnonzero(velocities)
    if active_indices.size == 0:
        return False

    rest_steps = np.empty(active_indices.size, dtype=np.int64)
    rest_steps[0] = active_indices[0]
    rest_steps[1:] = np.diff(active_indices) - 1
    note_on_times = rest_steps * step_ticks

    for idx, rest_ticks in zip(active_indices, note_on_times):
        pitches = notes_per_step[idx]
        velocity = int(velocities[idx])
        for j, pitch in enumerate(pitches):
            track.append(mido.Message('note_on', note=int(pitch), velocity=velocity, time=int(rest_ticks) if j == 0 else 0))
        for j, pitch in enumerate(pitches):
            track.append(mido.Message('note_off', note=int(pitch), velocity=0, time=step_ticks if j == 0 else 0))

    return True

def create_midi(notes_per_step, filename, velocities, step_ticks, time_signature):
    mid = mido.MidiFile(ticks_per_beat=TICKS_PER_QUARTER_NOTE)
    track = mido.MidiTrack()
    mid.tracks.append(track)

    track.append(mido.MetaMessage('track_name', name=filename, time=0))
    numerator, denominator = time_signature
    track.append(mido.MetaMessage('time_signature', numerator=numerator, denominator=denominator, time=0))

    if not append_note_events(track, notes_per_step, velocities, step_ticks):
        print(f"Skipping {filename}: no notes to play.")
        return

    filepath = os.path.join(OUTPUT_DIR, f"{filename}.mid")
    try:
        mid.save(filepath)
    except OSError as e:
        print(f"Error saving {filename}: {e}")

def create_ensemble_midi(ensemble_tracks, filename='ensemble_prime'):
    if not ensemble_tracks:
        return

    mid = mido.MidiFile(ticks_per_beat=TICKS_PER_QUARTER_NOTE)

    for i, (instrument_name, notes_per_step, velocities, step_ticks, time_signature) in enumerate(ensemble_tracks):
        track = mido.MidiTrack()
        track.append(mido.MetaMessage('track_name', name=instrument_name, time=0))
        if i == 0:
            numerator, denominator = time_signature
            track.append(mido.MetaMessage('time_signature', numerator=numerator, denominator=denominator, time=0))

        if append_note_events(track, notes_per_step, velocities, step_ticks):
            mid.tracks.append(track)

    if not mid.tracks:
        print(f"Skipping {filename}: no notes to play.")
        return

    filepath = os.path.join(OUTPUT_DIR, f"{filename}.mid")
    try:
        mid.save(filepath)
    except OSError as e:
        print(f"Error saving {filename}: {e}")

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

    elif relationship == 'union':
        sources = [base_binaries[name] for name in derives_from]
        binary = sources[0].copy()
        for s in sources[1:]:
            binary = binary | s
        return binary, len(binary)

    elif relationship == 'intersection':
        sources = [base_binaries[name] for name in derives_from]
        binary = sources[0].copy()
        for s in sources[1:]:
            binary = binary & s
        return binary, len(binary)

    elif relationship == 'xor':
        sources = [base_binaries[name] for name in derives_from]
        binary = sources[0].copy()
        for s in sources[1:]:
            binary = binary ^ s
        return binary, len(binary)

    elif relationship == 'difference':
        a = base_binaries[derives_from[0]]
        b = base_binaries[derives_from[1]]
        return a & (1 - b), len(a)

    elif relationship == 'stretch':
        src = base_binaries[derives_from]
        stretched = stretch_binary(src, config['factor'])
        return stretched, len(stretched)

    elif relationship == 'compress':
        src = base_binaries[derives_from]
        compressed = src[::config['factor']]
        return compressed, len(compressed)

    elif relationship == 'interleave':
        a = base_binaries[derives_from[0]]
        b = base_binaries[derives_from[1]]
        n = min(len(a), len(b))
        interleaved = np.where(np.arange(n) % 2 == 0, a[:n], b[:n])
        return interleaved, n

    elif relationship == 'majority':
        sources = [base_binaries[name] for name in derives_from]
        threshold = config.get('threshold', (len(sources) // 2) + 1)
        total = sum(sources)
        return (total >= threshold).astype(int), len(sources[0])

    raise ValueError(f"Unknown relationship: {relationship}")

def process_instrument(config, base_binary, period, ensemble_tracks):
    instrument_name = config.get('name', 'unnamed')

    accent_dict = config.get('accent_dict', {})
    accent_binaries = create_accent_binaries(accent_dict, period)

    if config.get('relationship') == 'shift':
        shift_amount = config.get('shift_amount', 0)
        accent_binaries = {label: np.roll(arr, shift_amount) for label, arr in accent_binaries.items()}

    velocity_profile = generate_velocity_profile(accent_dict, print_profile=bool(accent_dict))
    if not accent_dict and 'flat_velocity' in config:
        velocity_profile['gap'] = config['flat_velocity']

    step_ticks = get_step_ticks(config)
    time_signature = generate_time_signature(period, step_ticks)
    root_note = config.get('root', config.get('note', 64))
    chord_intervals = config.get('chord_intervals')

    all_transformations = ['prime'] + config.get('transformations', [])

    for t_name in all_transformations:
        try:
            t_func = get_transformation_func(t_name)
        except ValueError as e:
            print(f"Skipping transformation {t_name} for {instrument_name}: {e}")
            continue

        transformed_binary = t_func(base_binary)
        notes_per_step, velocities = accent_voicing(transformed_binary, accent_binaries, velocity_profile, root_note, chord_intervals)
        filename = f"{TITLE}_{instrument_name}_{t_name}"
        create_midi(notes_per_step, filename, velocities, step_ticks, time_signature)

        if t_name == 'prime':
            ensemble_tracks.append((instrument_name, notes_per_step, velocities, step_ticks, time_signature))

    if config.get('apply_shift', False):
        indices = np.nonzero(base_binary)[0]
        shift_direction = config.get('shift_direction', 'positive')

        for i in indices:
            if i == 0:
                continue

            s_values = []
            if shift_direction == 'positive':
                s_values = [i]
            elif shift_direction == 'negative':
                s_values = [-i]
            elif shift_direction == 'both':
                s_values = [i, -i]

            for s in s_values:
                shifted = np.roll(base_binary, s)
                shifted_accent_binaries = {
                    label: np.roll(arr, s) for label, arr in accent_binaries.items()
                }
                label = f"shift({s:+})"
                filename = f"{TITLE}_{instrument_name}_{label}"
                notes_per_step, velocities = accent_voicing(shifted, shifted_accent_binaries, velocity_profile, root_note, chord_intervals)
                create_midi(notes_per_step, filename, velocities, step_ticks, time_signature)

def main():
    ensure_directory(OUTPUT_DIR)
    clear_directory(OUTPUT_DIR)

    # Pass 1: build every binary in config order, including non-rendering
    # helpers, so later entries can derive from them by name.
    base_binaries = {}
    for config in INSTRUMENT_CONFIGS:
        binary, period = build_binary(config, base_binaries)
        base_binaries[config['name']] = binary

    # Pass 2: render only the entries that aren't marked render=False.
    ensemble_tracks = []
    for config in INSTRUMENT_CONFIGS:
        if not config.get('render', True):
            continue
        binary = base_binaries[config['name']]
        period = len(binary)
        process_instrument(config, binary, period, ensemble_tracks)

    create_ensemble_midi(ensemble_tracks, filename=f"{TITLE}_ensemble_prime")

if __name__ == '__main__':
    main()
