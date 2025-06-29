import os
import glob
import mido
import music21
import numpy as np
from config import *
from transformations import *

# Mapping transformation names to functions
TRANSFORMATION_MAP = {
    'prime': lambda x: x,
    'invert': invert_binary,
    'reverse': reverse_binary,
    'stretch_2': lambda x: stretch_binary(x, 2),
}

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
        return period//2, DURATION_TO_DENOMINATOR.get(duration, 16)
    else:
        return period, DURATION_TO_DENOMINATOR.get(duration, 16)

def create_accent_binaries(accent_dict, period):
    binaries = {}
    for label, pattern in accent_dict.items():
        s = music21.sieve.Sieve(pattern)
        s.setZRange(0, period - 1)
        binaries[label] = sieve_to_binary(s)
    return binaries

def accent_velocity(binary, primary_binary, secondary_binary, profile):
    velocities = []
    for i, bit in enumerate(binary):
        if not bit:
            velocities.append(0)
            continue
        p = primary_binary[i % len(primary_binary)]
        s = secondary_binary[i % len(secondary_binary)]
        if p and s:
            velocities.append(profile['overlap'])
        elif p:
            velocities.append(profile['primary'])
        elif s:
            velocities.append(profile['secondary'])
        else:
            velocities.append(profile['gap'])
    return velocities

def create_midi(binary, filename, velocities, note, duration_multiplier, time_signature):
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
    mid.save(filepath)
    print(f"Saved: {filepath}")

def process_instrument(config):
    instrument_name = config.get('name', 'unnamed')
    sieve_str = config['sieve']
    sieve = music21.sieve.Sieve(sieve_str)
    period = sieve.period()
    sieve.setZRange(0, period - 1)
    base_binary = sieve_to_binary(sieve)

    accent_dict = config.get('accent_dict', {})
    accent_binaries = create_accent_binaries(accent_dict, period)
    primary = accent_binaries.get('primary', np.zeros(period))
    secondary = accent_binaries.get('secondary', np.zeros(period))
    velocity_profile = config.get('velocity_profile', DEFAULT_VELOCITY_PROFILE)

    duration = config.get('duration', 'Quarter Note')
    duration_multiplier = get_duration_multiplier(duration)
    time_signature = generate_time_signature(period, duration)
    note = config.get('note', 64)

    # Always include 'prime'
    all_transformations = ['prime'] + config.get('transformations', [])

    # Apply transformations (including always-prime)
    for t_name in all_transformations:
        t_func = TRANSFORMATION_MAP[t_name]
        transformed_binary = t_func(base_binary)
        velocities = accent_velocity(transformed_binary, primary, secondary, velocity_profile)
        filename = f"{instrument_name}_{t_name}"
        create_midi(transformed_binary, filename, velocities, note, duration_multiplier, time_signature)

    # Apply shifts if requested
    if config.get('apply_shift', False):
        indices = np.nonzero(base_binary)[0]
        shift_direction = config.get('shift_direction', 'positive')  # NEW LINE
        for i in indices:
            if i == 0:
                continue  # Skip redundant shift(0), already generated as 'prime'

            shifts = []
            if shift_direction == 'positive':
                shifts = [i]
            elif shift_direction == 'negative':
                shifts = [-i]
            elif shift_direction == 'both':
                shifts = [i, -i]

            for s in shifts:
                shifted = np.roll(base_binary, s)
                label = f"shift(+{i})" if s > 0 else f"shift({s})"
                filename = f"{instrument_name}_{label}"
                velocities = accent_velocity(shifted, primary, secondary, velocity_profile)
                create_midi(shifted, filename, velocities, note, duration_multiplier, time_signature)

def main():
    ensure_directory(OUTPUT_DIR)
    clear_directory(OUTPUT_DIR)

    for config in INSTRUMENT_CONFIGS:
        process_instrument(config)

if __name__ == '__main__':
    main()