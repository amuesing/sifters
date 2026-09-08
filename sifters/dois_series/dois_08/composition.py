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
# Density envelope
# ---------------------------------------------------------------------------

def compute_density_envelope(binary, window_size):
    """Running window mean: at each position i, average binary over the
    symmetric window [i - half, i + half].  Endpoints are clamped, not
    wrapped, so the edge behaviour matches the linear nature of the piece."""
    period = len(binary)
    half   = window_size // 2
    envelope = np.zeros(period)
    for i in range(period):
        lo = max(0, i - half)
        hi = min(period, i + half + 1)
        envelope[i] = binary[lo:hi].mean()
    return envelope

def compute_form_plan(instrument_configs, micro_binaries, base_envelope):
    """Determine which instruments are active at each of the sieve's
    period sections.

    For section i:
      threshold_i = DENSITY_HIGH − (DENSITY_HIGH − DENSITY_LOW)
                      × (base_envelope[i] / base_envelope.max())

    An instrument is present when its own local window density at position i
    meets or exceeds threshold_i.  Testing against each instrument's own
    local density (not a global count) means voices enter and exit in
    proportion to their individual rhythmic density — dense voices first,
    sparse voices only at peak moments."""
    period  = len(base_envelope)
    d_max   = base_envelope.max()
    if d_max == 0:
        d_max = 1.0

    # Pre-compute each renderable instrument's density envelope.
    inst_envelopes = {}
    for config in instrument_configs:
        if not config.get('render', True):
            continue
        name = config['name']
        inst_envelopes[name] = compute_density_envelope(micro_binaries[name], ENVELOPE_WINDOW)

    form_plan = []
    for i in range(period):
        t_i = DENSITY_HIGH - (DENSITY_HIGH - DENSITY_LOW) * (base_envelope[i] / d_max)
        active = set()
        for name, env in inst_envelopes.items():
            if env[i] >= t_i:
                active.add(name)
        form_plan.append(active)

    return form_plan

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
        print(f"  Skipping {filename}: no active steps.")
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
# Density-modulated arrangement
# ---------------------------------------------------------------------------

def print_density_form(form_plan, ensemble_tracks, base_envelope):
    names   = [name for (name, *_) in ensemble_tracks]
    d_max   = base_envelope.max()
    n       = len(form_plan)

    print(f"\nDensity-modulated form  ({n} sections = one complete sieve traversal)")
    print(f"  {'Sec':>4}  {'BaseDens':>8}  {'Thresh':>6}  Active instruments")
    print(f"  {'-'*4}  {'-'*8}  {'-'*6}  {'-'*30}")

    t_range = DENSITY_HIGH - DENSITY_LOW
    for i, active in enumerate(form_plan):
        d_i = base_envelope[i]
        t_i = DENSITY_HIGH - t_range * (d_i / d_max)
        inst_str = '  '.join(n for n in names if n in active) or '[silence]'
        bar      = '█' * len(active)
        print(f"  {i:>4}  {d_i:>8.3f}  {t_i:>6.3f}  {inst_str:35s}  {bar}")

    print()
    print("  Instrument presence summary:")
    for name in names:
        count   = sum(1 for active in form_plan if name in active)
        pct     = 100 * count / n
        on_secs = [i for i, active in enumerate(form_plan) if name in active]
        print(f"    {name:10s}: {count:2d}/{n} sections ({pct:4.1f}%)  sections {on_secs}")
    print()

def create_density_arrangement(ensemble_tracks, form_plan, filename='arrangement'):
    if not ensemble_tracks:
        return

    cycle_lengths      = [len(binary) * step_ticks for (_, binary, _, _, step_ticks, _) in ensemble_tracks]
    base_section_ticks = math.lcm(*cycle_lengths)
    section_ticks      = base_section_ticks * SECTION_REPETITIONS

    ON, OFF = 1, 0
    mid = mido.MidiFile(ticks_per_beat=TICKS_PER_QUARTER_NOTE)

    for i, (name, binary, velocity, note, step_ticks, time_sig) in enumerate(ensemble_tracks):
        active_steps = np.flatnonzero(binary)
        if active_steps.size == 0:
            continue

        cycle_ticks = len(binary) * step_ticks
        reps        = section_ticks // cycle_ticks

        events = []
        for section_idx, active_names in enumerate(form_plan):
            if name not in active_names:
                continue
            sec_start = section_idx * section_ticks
            for rep in range(reps):
                rep_start = sec_start + rep * cycle_ticks
                for idx in active_steps:
                    on_tick  = rep_start + int(idx) * step_ticks
                    off_tick = on_tick + step_ticks
                    events.append((on_tick,  ON,  note, velocity))
                    events.append((off_tick, OFF, note, 0))

        if not events:
            print(f"  {name}: silent (never passed density threshold)")
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

    total_ticks = len(form_plan) * section_ticks
    total_qn    = total_ticks / TICKS_PER_QUARTER_NOTE
    print(f"Arrangement: {len(form_plan)} sections × {SECTION_REPETITIONS} rep × "
          f"{base_section_ticks} ticks"
          f" = {total_ticks} ticks ({total_qn:.0f} QN ≈ {total_qn / 120:.1f} min at 120 BPM)")

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

    # Pass 1 — micro: build note-level sieve binaries.
    micro_binaries = {}
    for config in INSTRUMENT_CONFIGS:
        binary, period = build_binary(config, micro_binaries)
        micro_binaries[config['name']] = binary

    print("Micro binary densities:")
    for config in INSTRUMENT_CONFIGS:
        name   = config['name']
        binary = micro_binaries[name]
        render = '' if config.get('render', True) else ' [helper]'
        print(f"  {name:12s}: {binary.sum():2d}/{len(binary)} steps "
              f"({100 * binary.mean():.1f}%){render}")

    # Pass 2 — render per-clip files and build ensemble.
    ensemble_tracks = []
    for config in INSTRUMENT_CONFIGS:
        if not config.get('render', True):
            continue
        binary = micro_binaries[config['name']]
        process_instrument(config, binary, len(binary), ensemble_tracks)

    create_ensemble_midi(ensemble_tracks, filename=f"{TITLE}_ensemble_prime")

    # Pass 3 — density envelope: running window mean of base sieve.
    base_envelope = compute_density_envelope(micro_binaries['base'], ENVELOPE_WINDOW)
    print(f"\nBase density envelope  (window={ENVELOPE_WINDOW}):")
    print(f"  range [{base_envelope.min():.3f}, {base_envelope.max():.3f}]  "
          f"→ threshold range [{DENSITY_HIGH - (DENSITY_HIGH - DENSITY_LOW):.3f}, {DENSITY_HIGH:.3f}]")

    # Pass 4 — form plan: gate each instrument at each section.
    form_plan = compute_form_plan(INSTRUMENT_CONFIGS, micro_binaries, base_envelope)
    print_density_form(form_plan, ensemble_tracks, base_envelope)

    # Pass 5 — render the arrangement.
    create_density_arrangement(ensemble_tracks, form_plan, filename=f"{TITLE}_arrangement")

if __name__ == '__main__':
    main()
