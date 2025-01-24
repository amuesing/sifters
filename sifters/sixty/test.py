# main.py
import os
import glob
import mido
import music21
import numpy as np

from config import (
    OUTPUT_DIR,
    TICKS_PER_QUARTER_NOTE,
    DEFAULT_VELOCITY_PROFILE,
    DURATION_MULTIPLIER_KEY,
    DURATION_TO_DENOMINATOR,
    INSTRUMENT_CONFIGS
)

def ensure_directory(path):
    os.makedirs(path, exist_ok=True)

def clear_directory(path):
    for file_path in glob.glob(f'{path}*'):
        os.remove(file_path)

def sieve_to_binary(sieve_obj):
    return np.array(sieve_obj.segment(segmentFormat='binary'))

def generate_time_signature(period, duration):
    if period > 255:
        raise ValueError(
            f"The period {period} exceeds the maximum allowed value of 255."
        )
    return period, DURATION_TO_DENOMINATOR.get(duration, 16)

def get_duration_multiplier(duration_name):
    return DURATION_MULTIPLIER_KEY.get(duration_name, 0.25)

def create_accent_binaries(accent_dict, period):
    accent_binaries = {}
    for key, pattern in accent_dict.items():
        if pattern:
            accent_binaries[key] = sieve_to_binary(music21.sieve.Sieve(pattern))
        else:
            accent_binaries[key] = np.zeros(period)
    return accent_binaries

def accent_velocity(base_binary, primary_binary, secondary_binary, velocity_profile):
    velocities = np.zeros(len(base_binary), dtype=int)
    for i, val in enumerate(base_binary):
        if val:
            p_hit = primary_binary[i % len(primary_binary)]
            s_hit = secondary_binary[i % len(primary_binary)]
            if p_hit and s_hit:
                velocities[i] = velocity_profile['overlap']
            elif p_hit:
                velocities[i] = velocity_profile['primary']
            elif s_hit:
                velocities[i] = velocity_profile['secondary']
            else:
                velocities[i] = velocity_profile['gap']
        else:
            velocities[i] = 0
    return velocities

def create_midi(binary, filename, velocities, note, duration_multiplier, time_signature):
    """
    Create a MIDI file but skip writing events for zero-velocity hits.
    Instead, we accumulate that duration as "rest time" and apply it
    to the delta time of the next note event.
    """
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)

    # Track name & time signature
    track.append(mido.MetaMessage('track_name', name=filename, time=0))
    numerator, denominator = time_signature
    track.append(mido.MetaMessage('time_signature', numerator=numerator, denominator=denominator, time=0))

    duration_ticks = int(TICKS_PER_QUARTER_NOTE * duration_multiplier)
    
    # We'll keep track of how many ticks of "rest" have accumulated
    accumulated_time = 0
    
    for is_on, vel in zip(binary, velocities):
        # If there's no hit (or vel == 0), accumulate rest
        if not is_on or vel == 0:
            accumulated_time += duration_ticks
        else:
            # We have a hit: apply the accumulated rest as delta time
            track.append(mido.Message('note_on', note=note, velocity=vel, time=accumulated_time))
            # The note lasts 'duration_ticks', then note_off
            track.append(mido.Message('note_off', note=note, velocity=vel, time=duration_ticks))
            
            # Reset accumulated_time after placing a note
            accumulated_time = 0

    filepath = os.path.join(OUTPUT_DIR, f"{filename}.mid")
    mid.save(filepath)

def process_sieve(config):
    sieve_str = config['sieve']
    sieve_obj = music21.sieve.Sieve(sieve_str)
    period = sieve_obj.period()
    sieve_obj.setZRange(0, period - 1)
    
    base_binary = sieve_to_binary(sieve_obj)
    
    accent_binaries = create_accent_binaries(config.get('accent_dict', {}), period)
    primary_binary = accent_binaries.get('primary', np.zeros(period))
    secondary_binary = accent_binaries.get('secondary', np.zeros(period))
    
    velocity_profile = config.get('velocity_profile', DEFAULT_VELOCITY_PROFILE)
    velocities = accent_velocity(base_binary, primary_binary, secondary_binary, velocity_profile)
    
    note = config.get('note', 64)
    duration = config.get('duration', 'Quarter Note')
    duration_multiplier = get_duration_multiplier(duration)
    time_signature = generate_time_signature(period, duration)
    
    filename = f"{sieve_str}_{duration}"
    
    print("Processing Sieve:", sieve_str)
    print("  --> Period =", period)
    print("  --> Duration =", duration)
    print("  --> Time Signature =", time_signature)
    print("  --> MIDI Filename =", filename + ".mid")
    
    create_midi(base_binary, filename, velocities, note, duration_multiplier, time_signature)

def main():
    ensure_directory(OUTPUT_DIR)
    clear_directory(OUTPUT_DIR)
    for config in INSTRUMENT_CONFIGS:
        process_sieve(config)

if __name__ == '__main__':
    main()