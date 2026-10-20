"""Serum wavetables from the sieve: every frame states one period, in its own register.

A single cycle has a harmonic series and the sieve has a period, so a frame can state
that period once, as harmonics:

    frame i reads the sieve from position i + 1 (h = 1 .. P) and sounds it from
    harmonic c + 1 upward, where the CUT is c = d * i mod P: harmonic c + h sounds, at
    full strength, when position i + h is in the voice's sieve; every other is silent.

Every member of the sieve sounds once in every frame. The reading gives 40 different
frames (the sieve's 40 rotations); the cut gives each its own REGISTER, which the ear
hears as brightness: cut 0 starts at the fundamental, cut 39 at harmonic 40. d is the
lattice's diagonal (13 for psappha), so neighbouring frames sit 13 harmonics apart and
the pitch lattice becomes a lattice of timbres. A sieve whose moduli share a factor has
no lattice; its cuts then go in order (d = 1).

The bound is two periods, harmonic 2P - 1 (79 for psappha). With pitch tracking off,
Serum plays the oscillator at MIDI note 0, 8.18 Hz, and OCT +4 takes it to 130.8 Hz;
harmonic 79 stays under Nyquist up to about 276 Hz.

One gain for the whole table: every frame has the same number of equal-strength
harmonics, so one gain set by the loudest peak keeps every frame at the same RMS, and
VELO changes colour, not loudness. Equal strength and one starting phase are the
conventions; the sieve supplies presence and absence.

128 frames, because notes and velocities run 0-127: with NOTE or VELO at its default
line, value v sits exactly on frame v. The SWEEP table follows the voice's parity
statement, frame k the frame for step k's velocity (0 at a rest), closing on its first.

Written as Serum 2 writes its own: 32-bit float, mono, 2048 samples a frame, and a
'clm ' chunk asking for no blending, with Serum's factory flag clear.
"""
import json
import math
import os
import shutil
import struct

import numpy as np

import config
from sieve import ancestral_moduli, diagonal

SAMPLE_RATE = 44100           # irrelevant to a wavetable's pitch; WAV needs one
PEAK = 0.95                   # headroom below full scale, for the loudest frame
MAX_FRAMES = 256              # Serum's limit
MIDI_VALUES = 128             # notes and velocities, 0..127: one frame each


def serum_marker():
    """The 'clm ' text: frame size, no blending (0), NOT a factory table (0)."""
    return f"<!>{config.WAVETABLE_FRAME_SAMPLES} 00000000 wavetable (www.xferrecords.com)"


def sidecar_text():
    """What Serum reads from `name.txt` beside a dragged `name.wav` (User Guide p. 295)."""
    return f"[{config.WAVETABLE_FRAME_SAMPLES}]\n[no interp]\n"


def frame_order(cfg, period):
    """d: how far apart neighbouring frames' cuts are. The lattice's diagonal when it is
    a unit modulo the voice's period, otherwise 1."""
    d = diagonal(ancestral_moduli(cfg, config.INSTRUMENT_CONFIGS))
    if d is None or math.gcd(d, period) != 1:
        return 1
    return d


def harmonics_for(rhythm, order, i):
    """Frame i's harmonics: the sieve read from i + 1, sounded from just above the cut."""
    period = len(rhythm)
    start = (order * i) % period
    return [start + h for h in range(1, period + 1) if rhythm[(i + h) % period]]


def frame_for(rhythm, order, i):
    """One single cycle before the table's gain: its harmonics, equal strength, in phase."""
    samples = config.WAVETABLE_FRAME_SAMPLES
    t = 2 * np.pi * np.arange(samples) / samples
    wave = np.zeros(samples)
    for m in harmonics_for(rhythm, order, i):
        wave += np.sin(m * t)
    return wave


def integer_frames(rhythm, order):
    """Frames for 0 .. 127 under ONE gain, so every frame keeps the same RMS."""
    frames = [frame_for(rhythm, order, i) for i in range(MIDI_VALUES)]
    gain = PEAK / max(np.max(np.abs(frame)) for frame in frames)
    return [gain * frame for frame in frames]


def sweep_frames(table, velocities):
    """The parity statement, one frame per step, closing on its first frame; None when
    it is longer than Serum's 256 frames allow."""
    steps = [int(v) for v in velocities]
    if len(steps) + 1 > MAX_FRAMES:
        return None
    return [table[v] for v in steps] + [table[steps[0]]]


def write_wav(path, frames):
    """Mono 32-bit float, frames back to back, laid out as Serum 2 writes its own."""
    data = np.concatenate(frames).astype('<f4').tobytes()
    marker = serum_marker().encode()
    if len(marker) % 2:
        marker += b'\0'
    fmt = struct.pack('<HHIIHH', 3, 1, SAMPLE_RATE, SAMPLE_RATE * 4, 4, 32)
    chunks = (b'fmt ' + struct.pack('<I', len(fmt)) + fmt
              + b'clm ' + struct.pack('<I', len(marker)) + marker
              + b'data' + struct.pack('<I', len(data)) + data)
    with open(path, 'wb') as handle:
        handle.write(b'RIFF' + struct.pack('<I', 4 + len(chunks)) + b'WAVE' + chunks)


def write_sidecar(directory, wav_name):
    """`name.txt` beside `name.wav`, so a drag-and-drop import knows the frame size."""
    name = os.path.splitext(wav_name)[0] + '.txt'
    with open(os.path.join(directory, name), 'w') as handle:
        handle.write(sidecar_text())
    return name


def write_wavetables(fields, base_binaries, prefix, directory):
    """Every voice's integer table and sweep. Returns the file names written."""
    written = []
    configs = {cfg['name']: cfg for cfg in config.INSTRUMENT_CONFIGS}
    for name, field in fields.items():
        rhythm = [int(x) for x in base_binaries[name]]
        period = len(rhythm)
        if 2 * period - 1 > config.WAVETABLE_FRAME_SAMPLES // 2 - 1:
            raise ValueError(f"{name}'s {period}-step period needs harmonics up to "
                             f"{2 * period - 1}, more than a "
                             f"{config.WAVETABLE_FRAME_SAMPLES}-sample frame holds "
                             f"without aliasing")
        order = frame_order(configs[name], period)
        table = integer_frames(rhythm, order)
        filename = f"{prefix}_wavetable_{name}.wav"
        write_wav(os.path.join(directory, filename), table)
        written += [filename, write_sidecar(directory, filename)]
        how = (f"registers {order} harmonics apart — the lattice's diagonal" if order != 1
               else "cuts in order — this sieve's moduli share a factor, so it has no "
                    "lattice diagonal")
        print(f"  Saved: {filename}  ({MIDI_VALUES} frames, one per note or velocity value; "
              f"{period} cuts, {how}; harmonics 1-{2 * period - 1})")

        if config.SERUM_PRESETS:
            # The voice's complement, by the same rule: the FM pairs' modulator.
            filename = f"{prefix}_wavetable_not_{name}.wav"
            write_wav(os.path.join(directory, filename),
                      integer_frames([1 - x for x in rhythm], order))
            written += [filename, write_sidecar(directory, filename)]
            print(f"  Saved: {filename}  (its complement: every step {name} leaves out, by the "
                  f"same rule)")

        if config.WAVETABLE_SWEEP:
            frames = sweep_frames(table, field['velocities'])
            if frames is None:
                print(f"  -- {name}: no sweep table; its {len(field['velocities'])}-step "
                      f"statement needs more than Serum's {MAX_FRAMES} frames")
                continue
            filename = f"{prefix}_wavetable_{name}_sweep.wav"
            write_wav(os.path.join(directory, filename), frames)
            written += [filename, write_sidecar(directory, filename)]
            print(f"  Saved: {filename}  ({len(frames)} frames — the parity statement, "
                  f"each step at its velocity's frame, closing on its first)")
    return written


# ---------------------------------------------------------------- installing into Serum

SERUM_PREFS = os.path.expanduser('~/Library/Preferences/Serum2Prefs.json')
SERUM_DEFAULT = '/Library/Audio/Presets/Xfer Records/Serum 2 Presets'


def serum_presets_folder(prefs_path=SERUM_PREFS):
    """The presets folder THIS Serum uses, read from its own preferences: a user can
    move it from the installer's /Library default (this user's lives in Documents)."""
    try:
        with open(prefs_path) as handle:
            path = json.load(handle).get('Serum Presets Path', '')
    except (OSError, ValueError):
        return SERUM_DEFAULT
    return path.rstrip('/') or SERUM_DEFAULT


def serum_folder():
    """The folder in Serum's menus: the version, and beside it a piece's own title, so no
    two versions' files ever share a folder: `dois_46`, `dois_46 eight_five`."""
    if config.TITLE == config.VERSION:
        return config.VERSION
    return f"{config.VERSION} {config.TITLE}"


def serum_tables_folder(presets=None):
    """`Tables/<project>/<folder>`: one `sifters` folder in Serum's menu, a labelled folder
    inside it, at the same depth as Serum 2's own `Tables/S2 Tables/Analog`."""
    return os.path.join(presets or serum_presets_folder(), 'Tables',
                        config.SERUM_PROJECT, serum_folder())


def clear_folder(folder, extension):
    """Remove the files of one kind from one folder of ours, so installing replaces the
    folder's contents instead of merging into them. Nothing else is touched."""
    if not os.path.isdir(folder):
        return []
    removed = sorted(f for f in os.listdir(folder) if f.endswith(extension))
    for name in removed:
        os.remove(os.path.join(folder, name))
    return removed


def installed_name(filename):
    """`dois_46_wavetable_A_sweep.wav` -> `A sweep.wav`, `..._not_A.wav` -> `not A.wav`."""
    stem = os.path.splitext(filename)[0].removeprefix(f"{config.TITLE}_wavetable_")
    return stem.replace('_', ' ') + '.wav'


def install_into_serum(source_dir, filenames, target_dir):
    """Copy finished wavetables into Serum's `Tables/<project>/<folder>`, replacing what
    that folder held. Only `compose.py --install-serum` calls this; nothing else writes
    outside the project."""
    parts = os.path.normpath(target_dir).split(os.sep)
    if len(parts) < 3 or parts[-3] != 'Tables':
        raise ValueError(f"{target_dir} is not Tables/<project>/<version> inside a Serum "
                         f"presets folder; Serum would not list it where it belongs")
    clear_folder(target_dir, '.wav')
    os.makedirs(target_dir, exist_ok=True)
    copied = []
    for name in filenames:
        if name.endswith('.wav'):
            target = installed_name(name)
            shutil.copyfile(os.path.join(source_dir, name), os.path.join(target_dir, target))
            copied.append(target)
    return copied
