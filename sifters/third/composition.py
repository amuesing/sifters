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
    for file_path in glob.glob(f'{path}*'):
        os.remove(file_path)

def sieve_to_binary(sieve_obj):
    return np.array(sieve_obj.segment(segmentFormat='binary'))

def get_duration_multiplier(duration_name):
    return DURATION_MULTIPLIER_KEY.get(duration_name, 0.25)

def generate_time_signature(period, duration):
    if period > 255:
        raise ValueError(f"The period {period} exceeds 255.")
    if duration == 'Thirty-Second Note':
        return period // 2, DURATION_TO_DENOMINATOR.get(duration, 16)
    return period, DURATION_TO_DENOMINATOR.get(duration, 16)

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
        return {}

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

# Use numpy to accelerate velocity assignment
def accent_velocity(binary, accent_binaries, profile):
    active_labels_array = np.zeros_like(binary, dtype=object)  # Will store active labels at each index

    # Precompute active labels for each index
    for i in range(len(binary)):
        active_labels_array[i] = [
            label for label, arr in accent_binaries.items() if arr[i % len(arr)]
        ]
    
    velocities = np.zeros_like(binary, dtype=int)  # Store the velocity for each index

    # Using vectorized operations for velocity assignment
    for i, active_labels in enumerate(active_labels_array):
        if not binary[i]:
            velocities[i] = 0
        elif len(active_labels) > 1:
            velocities[i] = profile['overlap']
        elif len(active_labels) == 1:
            velocities[i] = profile.get(active_labels[0], profile['gap'])
        else:
            velocities[i] = profile['gap']

    return velocities

def create_midi(binary, filename, velocities, note, duration_multiplier, time_signature):
    if not np.any(binary) or not np.any(velocities):
        print(f"Skipping {filename}: no notes to play.")
        return

    mid = mido.MidiFile(ticks_per_beat=TICKS_PER_QUARTER_NOTE)
    track = mido.MidiTrack()
    mid.tracks.append(track)

    track.append(mido.MetaMessage('track_name', name=filename, time=0))
    numerator, denominator = time_signature
    track.append(mido.MetaMessage('time_signature', numerator=numerator, denominator=denominator, time=0))

    step_ticks = int(TICKS_PER_QUARTER_NOTE * duration_multiplier)
    accumulated_time = 0

    # Use numpy to avoid multiple individual `note_on`/`note_off` calls
    for val, vel in zip(binary, velocities):
        if val:
            track.append(mido.Message('note_on', note=note, velocity=vel, time=accumulated_time))
            track.append(mido.Message('note_off', note=note, velocity=0, time=step_ticks))
            accumulated_time = 0
        else:
            accumulated_time += step_ticks

    filepath = os.path.join(OUTPUT_DIR, f"{filename}.mid")
    try:
        mid.save(filepath)
        # print(f"Saved: {filepath}")
    except Exception as e:
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

def process_instrument(config):
    instrument_name = config.get('name', 'unnamed')
    sieve_str = config['sieve']
    sieve = music21.sieve.Sieve(sieve_str)
    period = sieve.period()
    sieve.setZRange(0, period - 1)
    base_binary = sieve_to_binary(sieve)

    accent_dict = config.get('accent_dict', {})
    accent_binaries = create_accent_binaries(accent_dict, period)
    velocity_profile = generate_velocity_profile(accent_dict, print_profile=True)

    duration = config.get('duration', 'Quarter Note')
    duration_multiplier = get_duration_multiplier(duration)
    time_signature = generate_time_signature(period, duration)
    note = config.get('note', 64)

    all_transformations = ['prime'] + config.get('transformations', [])

    for t_name in all_transformations:
        try:
            t_func = get_transformation_func(t_name)
            transformed_binary = t_func(base_binary)
            velocities = accent_velocity(transformed_binary, accent_binaries, velocity_profile)
            filename = f"{instrument_name}_{t_name}"
            create_midi(transformed_binary, filename, velocities, note, duration_multiplier, time_signature)
        except Exception as e:
            print(f"Skipping transformation {t_name} for {instrument_name}: {e}")

    if config.get('apply_shift', False):
        indices = np.nonzero(base_binary)[0]
        shift_direction = config.get('shift_direction', 'positive')

        for i in indices:
            if i == 0:
                continue  # Skip shift of 0

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
                filename = f"{instrument_name}_{label}"
                velocities = accent_velocity(shifted, shifted_accent_binaries, velocity_profile)
                create_midi(shifted, filename, velocities, note, duration_multiplier, time_signature)

def main():
    ensure_directory(OUTPUT_DIR)
    clear_directory(OUTPUT_DIR)

    for config in INSTRUMENT_CONFIGS:
        process_instrument(config)

if __name__ == '__main__':
    main()