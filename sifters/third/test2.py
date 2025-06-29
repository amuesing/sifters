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
    else:
        return period, DURATION_TO_DENOMINATOR.get(duration, 16)

def create_accent_binaries(accent_dict, period):
    binaries = {}
    for label, pattern in accent_dict.items():
        s = music21.sieve.Sieve(pattern)
        s.setZRange(0, period - 1)
        binaries[label] = sieve_to_binary(s)
    return binaries

def generate_velocity_profile(accent_labels, print_velocities=False, instrument_name=''):
    n = len(accent_labels)
    min_vel = 1
    max_vel = 127

    if n == 1:
        values = [(min_vel + max_vel) // 2]
    else:
        step = (max_vel - min_vel) / (n + 1)
        values = [round(min_vel + step * (i + 1)) for i in range(n)]

    profile = {label: vel for label, vel in zip(accent_labels, values)}
    profile['gap'] = min_vel
    profile['overlap'] = max_vel

    if print_velocities:
        print(f"\nVelocity profile for '{instrument_name}':")
        for label, vel in profile.items():
            print(f"  {label}: {vel}")

    return profile

def accent_velocity(binary, accent_binaries, profile):
    velocities = []
    n = len(binary)
    accent_arrays = list(accent_binaries.values())
    accent_labels = list(accent_binaries.keys())

    for i in range(n):
        if not binary[i]:
            velocities.append(profile['gap'])
            continue

        active_labels = [label for label, arr in zip(accent_labels, accent_arrays) if arr[i % len(arr)]]

        if len(active_labels) >= 2:
            velocities.append(profile['overlap'])
        elif len(active_labels) == 1:
            velocities.append(profile[active_labels[0]])
        else:
            velocities.append(profile['gap'])

    return velocities

def create_midi(binary, filename, velocities, note, duration_multiplier, time_signature):
    if not any(binary) or not any(velocities):
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
        print(f"Saved: {filepath}")
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
    accent_labels = list(accent_dict.keys())
    accent_binaries = create_accent_binaries(accent_dict, period)
    velocity_profile = generate_velocity_profile(accent_labels, print_velocities=True, instrument_name=instrument_name)

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
        seen_shifts = set()

        for i in indices:
            if i == 0 or i >= period:
                continue

            s_values = []
            if shift_direction == 'positive':
                s_values = [i]
            elif shift_direction == 'negative':
                s_values = [-i]
            elif shift_direction == 'both':
                s_values = [i, -i]

            for s in s_values:
                s_mod = s % period
                if s_mod in seen_shifts:
                    continue
                seen_shifts.add(s_mod)

                shifted = np.roll(base_binary, s)
                label = f"shift({s:+})"
                filename = f"{instrument_name}_{label}"
                velocities = accent_velocity(shifted, accent_binaries, velocity_profile)
                create_midi(shifted, filename, velocities, note, duration_multiplier, time_signature)

def main():
    ensure_directory(OUTPUT_DIR)
    clear_directory(OUTPUT_DIR)

    for config in INSTRUMENT_CONFIGS:
        process_instrument(config)

if __name__ == '__main__':
    main()