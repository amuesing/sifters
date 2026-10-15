"""Serum wavetables from the sieve: one frame for every whole number a note or velocity can be.

dois_40. A note number is a whole number, a velocity is a whole number, and a sieve is a
rule about whole numbers — so the sieve itself can say what each one sounds like:

    the frame for whole number i:
        harmonic h sounds, at full strength, if i + h is in the voice's sieve,
        for h = 1 .. the sieve's period; every other harmonic is silent.

That is the whole construction. Frame i reads one period of the sieve, starting just after
i, as a set of harmonics: the period stated exactly once, in frequency, as Principle I asks
of duration. There is no rolloff, no emphasis, no smoothing and no forced fundamental — each
was a choice in dois_37-39, and each made the frames more alike. Every harmonic starts in
phase, in every frame, and each frame is scaled to the same peak so frames differ in
colour, not level.

Why it gives variety: neighbouring whole numbers read the sieve one step apart, so the set
of harmonics changes at every step — including whether the fundamental and the lowest
harmonics are there at all. Measured on psappha: neighbouring frames differ by 39-45 dB
(a missing harmonic counted as missing), against roughly 1-5 dB for dois_39.

Why 128 frames: MIDI notes and velocities run 0 to 127. With Serum's NOTE or VELO at its
default straight line, value v sits v/127 of the way through the table, which is exactly
frame v. So:

  * NOTE -> WT POS, pitch tracking OFF: each note picks its own timbre. The lattice set's
    notes cover every residue of the sieve's period, so every lattice step gets its own;
  * VELO -> WT POS: each accent state's velocity picks its own timbre.

The table repeats every period (40 frames here): the sieve does. The voices' relationships
carry over — B, the complement, holds exactly the harmonics A lacks; C, the canon, holds A's
timbres 13 frames along; D, the intersection, is sparser.

The SWEEP table follows the voice's whole parity statement: frame k is the frame for the
velocity the piece gives step k (0 at a rest), and it ends on its first frame again, so a
ramp of WT POS across the clip puts each step's timbre on its step.

Files are written as Serum 2's own wavetables are — 32-bit float, mono, 2048 samples a
frame — with a 'clm ' chunk '<!>2048 00000000 wavetable (...)': no blending between
frames, and Serum's factory flag clear, as it must be for a custom table.
"""
import json
import os
import shutil
import struct

import numpy as np

import config

SAMPLE_RATE = 44100           # irrelevant to a wavetable's pitch; WAV needs one
PEAK = 0.95                   # headroom below full scale
MAX_FRAMES = 256              # Serum's limit
MIDI_VALUES = 128             # notes and velocities, 0..127: one frame each


def serum_marker():
    """The 'clm ' text: frame size, no blending (0), NOT a factory table (0)."""
    return f"<!>{config.WAVETABLE_FRAME_SAMPLES} 00000000 wavetable (www.xferrecords.com)"


def sidecar_text():
    """What Serum reads from `name.txt` beside a dragged `name.wav` (User Guide p. 295)."""
    return f"[{config.WAVETABLE_FRAME_SAMPLES}]\n[no interp]\n"


def harmonics_for(rhythm, i):
    """The harmonics frame i sounds: h such that i + h is in the sieve, h = 1 .. period."""
    period = len(rhythm)
    return [h for h in range(1, period + 1) if rhythm[(i + h) % period]]


def frame_for(rhythm, i):
    """One single cycle: the harmonics of whole number i, equal strength, in phase."""
    samples = config.WAVETABLE_FRAME_SAMPLES
    t = 2 * np.pi * np.arange(samples) / samples
    present = harmonics_for(rhythm, i)
    wave = np.zeros(samples)
    for h in present:
        wave += np.sin(h * t)
    return PEAK * wave / np.max(np.abs(wave))


def integer_frames(rhythm):
    """Frames for 0 .. 127, so a note number or a velocity lands exactly on its own."""
    return [frame_for(rhythm, i) for i in range(MIDI_VALUES)]


def sweep_frames(table, velocities):
    """The voice's parity statement, one frame per step, closing on its first frame.

    Returns None when the statement is longer than Serum's 256 frames allow.
    """
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
    for name, field in fields.items():
        rhythm = [int(x) for x in base_binaries[name]]
        if len(rhythm) > config.WAVETABLE_FRAME_SAMPLES // 2 - 1:
            raise ValueError(f"{name}'s {len(rhythm)}-step period needs that many "
                             f"harmonics, more than a {config.WAVETABLE_FRAME_SAMPLES}-"
                             f"sample frame holds without aliasing")
        table = integer_frames(rhythm)
        filename = f"{prefix}_wavetable_{name}.wav"
        write_wav(os.path.join(directory, filename), table)
        written += [filename, write_sidecar(directory, filename)]
        distinct = len({tuple(harmonics_for(rhythm, i)) for i in range(MIDI_VALUES)})
        print(f"  Saved: {filename}  ({MIDI_VALUES} frames, one per note or velocity value; "
              f"{distinct} distinct timbres — the sieve's period)")

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
    """The presets folder THIS Serum uses, read from its own preferences.

    Serum's installer puts presets in /Library, but a user can move them — this user's
    live in Documents. dois_39 assumed the default and installed where Serum never looked.
    """
    try:
        with open(prefs_path) as handle:
            path = json.load(handle).get('Serum Presets Path', '')
    except (OSError, ValueError):
        return SERUM_DEFAULT
    return path.rstrip('/') or SERUM_DEFAULT


def serum_tables_folder(presets=None):
    """`Tables/<project> <version>` — one top-level folder per project and version.

    Serum scans folders directly inside Tables and no deeper (User Guide p. 345), so the
    project and the version share one folder name rather than nesting.
    """
    return os.path.join(presets or serum_presets_folder(), 'Tables',
                        f"{config.SERUM_PROJECT} {config.TITLE}")


def installed_name(filename):
    """`dois_40_wavetable_A_sweep.wav` -> `A sweep.wav`: the folder already says the rest."""
    stem = os.path.splitext(filename)[0].removeprefix(f"{config.TITLE}_wavetable_")
    return stem.replace('_', ' ') + '.wav'


def install_into_serum(source_dir, filenames, target_dir):
    """Copy finished wavetables into Serum, so they appear in its wavetable menu.

    `target_dir` must sit DIRECTLY inside a Serum `Tables` folder. Only the given tables are
    written; nothing else there is touched. Called only from `compose.py --install-serum`,
    never by a plain render, so no test or ordinary run writes outside the project.
    """
    if os.path.basename(os.path.dirname(os.path.normpath(target_dir))) != 'Tables':
        raise ValueError(f"{target_dir} is not directly inside a Serum 'Tables' folder; "
                         f"Serum would not find tables there")
    os.makedirs(target_dir, exist_ok=True)
    copied = []
    for name in filenames:
        if name.endswith('.wav'):
            target = installed_name(name)
            shutil.copyfile(os.path.join(source_dir, name), os.path.join(target_dir, target))
            copied.append(target)
    return copied
