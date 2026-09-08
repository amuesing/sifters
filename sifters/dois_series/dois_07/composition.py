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
    for file_path in glob.glob(os.path.join(path, '*.mid')):
        os.remove(file_path)

def sieve_to_binary(sieve_obj):
    return np.array(sieve_obj.segment(segmentFormat='binary'))

def get_step_ticks(config):
    duration = config.get('duration', 'Sixteenth Note')
    return int(TICKS_PER_QUARTER_NOTE * DURATION_MULTIPLIER_KEY.get(duration, 0.25))

def generate_time_signature(period, step_ticks):
    if period > 255:
        raise ValueError(f"Period {period} exceeds 255.")
    denominator = STEP_TICKS_TO_DENOMINATOR.get(step_ticks, 16)
    if step_ticks == 60:
        return period // 2, denominator
    return period, denominator

def build_binary(config, base_binaries):
    if 'sieve' in config:
        sieve = music21.sieve.Sieve(config['sieve'])
        period = sieve.period()
        sieve.setZRange(0, period - 1)
        return sieve_to_binary(sieve), period

    relationship = config.get('relationship')
    derives_from  = config['derives_from']

    if relationship == 'complement':
        src = base_binaries[derives_from]
        return 1 - src, len(src)

    elif relationship == 'shift':
        src = base_binaries[derives_from]
        return np.roll(src, config['shift_amount']), len(src)

    elif relationship == 'union':
        sources = [base_binaries[n] for n in derives_from]
        result = sources[0].copy()
        for s in sources[1:]: result = result | s
        return result, len(result)

    elif relationship == 'intersection':
        sources = [base_binaries[n] for n in derives_from]
        result = sources[0].copy()
        for s in sources[1:]: result = result & s
        return result, len(result)

    elif relationship == 'xor':
        sources = [base_binaries[n] for n in derives_from]
        result = sources[0].copy()
        for s in sources[1:]: result = result ^ s
        return result, len(result)

    elif relationship == 'majority':
        sources = [base_binaries[n] for n in derives_from]
        threshold = config.get('threshold', (len(sources) // 2) + 1)
        return (sum(sources) >= threshold).astype(int), len(sources[0])

    raise ValueError(f"Unknown relationship: {relationship}")

# ---------------------------------------------------------------------------
# Fractal downsampling
# ---------------------------------------------------------------------------

def downsample_binary(binary, z_range, threshold):
    """Window-average downsampling: divide the micro binary into z_range equal
    windows; a window is active if its mean density >= threshold.
    Each instrument uses its own micro density as the threshold so both
    voices have comparable footprints in the form regardless of how many
    steps they each occupy at the note level."""
    period = len(binary)
    result = np.zeros(z_range, dtype=int)
    for i in range(z_range):
        lo = int(i * period / z_range)
        hi = int((i + 1) * period / z_range)
        if hi > lo and binary[lo:hi].mean() >= threshold:
            result[i] = 1
    return result

def build_all_presences(instrument_configs, micro_binaries, z_range):
    """Downsample every instrument's own micro binary to z_range.
    Threshold defaults to PRESENCE_THRESHOLD; override per-instrument
    with 'presence_threshold': 0.x in the config dict."""
    presences = {}
    for config in instrument_configs:
        name      = config['name']
        threshold = config.get('presence_threshold', PRESENCE_THRESHOLD)
        presences[name] = downsample_binary(micro_binaries[name], z_range, threshold)
    return presences

# ---------------------------------------------------------------------------
# MIDI rendering
# ---------------------------------------------------------------------------

def append_note_events(track, binary, velocity, note, step_ticks):
    active_indices = np.flatnonzero(binary)
    if active_indices.size == 0:
        return False

    rest_steps = np.empty(active_indices.size, dtype=np.int64)
    rest_steps[0] = active_indices[0]
    rest_steps[1:] = np.diff(active_indices) - 1

    for idx, rest in zip(active_indices, rest_steps * step_ticks):
        track.append(mido.Message('note_on',  note=note, velocity=velocity, time=int(rest)))
        track.append(mido.Message('note_off', note=note, velocity=0,        time=step_ticks))

    # Pad to the full period so the clip loops at the correct length in Ableton.
    full_ticks = len(binary) * step_ticks
    last_off   = (int(active_indices[-1]) + 1) * step_ticks
    remaining  = full_ticks - last_off
    if remaining > 0:
        track.append(mido.MetaMessage('end_of_track', time=remaining))

    return True

def create_midi(binary, filename, velocity, note, step_ticks, time_signature):
    mid   = mido.MidiFile(ticks_per_beat=TICKS_PER_QUARTER_NOTE)
    track = mido.MidiTrack()
    mid.tracks.append(track)

    track.append(mido.MetaMessage('track_name', name=filename, time=0))
    num, den = time_signature
    track.append(mido.MetaMessage('time_signature', numerator=num, denominator=den, time=0))

    if not append_note_events(track, binary, velocity, note, step_ticks):
        print(f"Skipping {filename}: no active steps.")
        return

    filepath = os.path.join(OUTPUT_DIR, f"{filename}.mid")
    try:
        mid.save(filepath)
    except OSError as e:
        print(f"Error saving {filename}: {e}")

def create_ensemble_midi(ensemble_tracks, filename='ensemble_prime'):
    mid = mido.MidiFile(ticks_per_beat=TICKS_PER_QUARTER_NOTE)

    for i, (name, binary, velocity, note, step_ticks, time_sig) in enumerate(ensemble_tracks):
        track = mido.MidiTrack()
        track.append(mido.MetaMessage('track_name', name=name, time=0))
        if i == 0:
            num, den = time_sig
            track.append(mido.MetaMessage('time_signature', numerator=num, denominator=den, time=0))
        if append_note_events(track, binary, velocity, note, step_ticks):
            mid.tracks.append(track)

    if not mid.tracks:
        return

    filepath = os.path.join(OUTPUT_DIR, f"{filename}.mid")
    try:
        mid.save(filepath)
    except OSError as e:
        print(f"Error saving {filename}: {e}")

def process_instrument(config, binary, period, ensemble_tracks):
    name       = config['name']
    note       = config.get('root', 60)
    velocity   = config.get('flat_velocity', 80)
    step_ticks = get_step_ticks(config)
    time_sig   = generate_time_signature(period, step_ticks)

    create_midi(binary, f"{TITLE}_{name}_prime", velocity, note, step_ticks, time_sig)
    ensemble_tracks.append((name, binary, velocity, note, step_ticks, time_sig))

# ---------------------------------------------------------------------------
# Fractal arrangement
# ---------------------------------------------------------------------------

def print_form_plan(meso_presences, macro_presences, names):
    print(f"\nFractal form plan")
    print(f"  Micro  : {len(list(meso_presences.values())[0]) * 40 // len(list(meso_presences.values())[0])}-step sieve rhythm (natural period)")
    print(f"  Macro  ({NUM_MOVEMENTS} movements, downsampled from micro):")
    for name in names:
        active = np.flatnonzero(macro_presences[name]).tolist()
        print(f"    {name:14s}: movements {active}")
    print(f"  Meso   ({NUM_SECTIONS_PER_MOVEMENT} sections/movement, downsampled from micro):")
    for name in names:
        active = np.flatnonzero(meso_presences[name]).tolist()
        print(f"    {name:14s}: sections  {active}")
    print(f"  Combined global [movement, section] positions:")
    for name in names:
        active = [
            (m, s)
            for m in range(NUM_MOVEMENTS)          if macro_presences[name][m]
            for s in range(NUM_SECTIONS_PER_MOVEMENT) if meso_presences[name][s]
        ]
        print(f"    {name:14s}: {active}")
    print()

def create_fractal_arrangement(ensemble_tracks, meso_presences, macro_presences, filename='arrangement'):
    if not ensemble_tracks:
        return

    names = [name for (name, *_) in ensemble_tracks]
    print_form_plan(meso_presences, macro_presences, names)

    cycle_lengths      = [len(binary) * step_ticks for (_, binary, _, _, step_ticks, _) in ensemble_tracks]
    base_section_ticks = math.lcm(*cycle_lengths)
    section_ticks      = base_section_ticks * SECTION_REPETITIONS

    ON, OFF = 1, 0
    mid = mido.MidiFile(ticks_per_beat=TICKS_PER_QUARTER_NOTE)

    for i, (name, binary, velocity, note, step_ticks, time_sig) in enumerate(ensemble_tracks):
        macro_bin = macro_presences.get(name, np.zeros(NUM_MOVEMENTS, dtype=int))
        meso_bin  = meso_presences.get(name,  np.zeros(NUM_SECTIONS_PER_MOVEMENT, dtype=int))

        cycle_ticks  = len(binary) * step_ticks
        reps         = section_ticks // cycle_ticks
        active_steps = np.flatnonzero(binary)
        if active_steps.size == 0:
            continue

        events = []
        for m in range(NUM_MOVEMENTS):
            if not macro_bin[m]:
                continue
            mov_start = m * NUM_SECTIONS_PER_MOVEMENT * section_ticks
            for s in range(NUM_SECTIONS_PER_MOVEMENT):
                if not meso_bin[s]:
                    continue
                sec_start = mov_start + s * section_ticks
                for rep in range(reps):
                    rep_start = sec_start + rep * cycle_ticks
                    for idx in active_steps:
                        on_tick  = rep_start + int(idx) * step_ticks
                        off_tick = on_tick + step_ticks
                        events.append((on_tick,  ON,  note, velocity))
                        events.append((off_tick, OFF, note, 0))

        if not events:
            print(f"  {name}: silent (no active macro×meso positions)")
            continue

        events.sort(key=lambda e: (e[0], e[1]))

        track = mido.MidiTrack()
        track.append(mido.MetaMessage('track_name', name=name, time=0))
        if i == 0:
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
          f"= {total_ticks} ticks ({total_qn:.0f} quarter notes "
          f"≈ {total_qn / 120:.1f} min at 120 BPM)")

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

    # Pass 1 — micro: build the note-level sieve binaries.
    micro_binaries = {}
    for config in INSTRUMENT_CONFIGS:
        binary, period = build_binary(config, micro_binaries)
        micro_binaries[config['name']] = binary

    # Print micro-level density.
    print("Micro binary densities:")
    for name, binary in micro_binaries.items():
        print(f"  {name:14s}: {binary.sum()}/{len(binary)} active steps")

    # Pass 2 — render per-clip files (session-view library).
    ensemble_tracks = []
    for config in INSTRUMENT_CONFIGS:
        if not config.get('render', True):
            continue
        binary = micro_binaries[config['name']]
        process_instrument(config, binary, len(binary), ensemble_tracks)

    create_ensemble_midi(ensemble_tracks, filename=f"{TITLE}_ensemble_prime")

    # Pass 3 — meso: downsample micro binary to NUM_SECTIONS_PER_MOVEMENT points.
    meso_presences = build_all_presences(INSTRUMENT_CONFIGS, micro_binaries, NUM_SECTIONS_PER_MOVEMENT)

    # Pass 4 — macro: downsample micro binary to NUM_MOVEMENTS points.
    macro_presences = build_all_presences(INSTRUMENT_CONFIGS, micro_binaries, NUM_MOVEMENTS)

    # Pass 5 — render the fractal arrangement.
    create_fractal_arrangement(ensemble_tracks, meso_presences, macro_presences, filename=f"{TITLE}_arrangement")

if __name__ == '__main__':
    main()
