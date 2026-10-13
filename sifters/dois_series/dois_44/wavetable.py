"""Serum wavetables from the sieve: every frame states one period, in its own register.

dois_41. A single cycle has a harmonic series, and the sieve has a period, so a frame can
state that period once, as harmonics:

    frame i reads one period of the sieve starting just after i — position i + h for
    h = 1 .. P, as dois_40 did — and sounds it from harmonic c + 1 upward, where the CUT
    is c = d * i mod P. Harmonic c + h sounds, at full strength, when position i + h is
    in the voice's sieve; every other harmonic is silent.

Every member of the sieve sounds exactly once in every frame — the period is stated
once, in frequency, as Principle I asks of duration. The reading gives each frame its own
pattern: the sieve has 40 different rotations, so the table has 40 different frames. The
cut gives each frame its own REGISTER: cut 0 starts at the fundamental; cut 39 starts at
harmonic 40, a high band with no fundamental. Register is what the ear hears as
brightness, and it is what dois_40 lacked.

A cut alone, reading residue m mod P at harmonic m, was tried first. It changes a frame
only when the cut crosses a member of the sieve, so a voice gets as many distinct frames
as it has attacks — 13 for B, whose velocity states then shared a frame. Reading from i
keeps all 40.

d is the lattice's diagonal, sum(P/m) over the sieve's moduli: 8 + 5 = 13 for psappha —
the same number that turns steps into pitches in the lattice, and C's canon distance.
Neighbouring frames are therefore 13 harmonics apart in register rather than one, so
scrubbing the table moves a long way at every frame. A sieve whose moduli share a factor has no lattice; its
frames then follow the cut in order (d = 1), and the render says so.

Why dois_40 sounded alike although its frames all differed: every frame put its harmonics
in 1..40, so all 128 frames had the same register — brightness moved 0.17 of an octave
across the whole table. Measured on psappha's A, this rule moves it 1.53 octaves across
the table and 0.55 octave between neighbouring frames; successive notes of the lattice
melody move 0.62 octave.

The bound is two periods: harmonic 2P - 1 at most, 79 for psappha. With pitch tracking
off, Serum plays a wavetable at a fixed pitch the User Guide does not state; at middle C
(261.6 Hz) harmonic 79 is 20.7 kHz, still under Nyquist at 44.1 kHz. The leap prototypes
installed before dois_41 reached harmonic 166, so at that pitch about a third of their
frames would have sounded nothing.

One gain for the whole table. Every frame has the same number of equal-strength
harmonics — one per residue in the sieve — so every frame has the same RMS. dois_40
scaled each frame to its own peak, which moved the level 0.4-1.2 dB between velocity
frames (ChatGPT, 2026-10-12). One gain, set by the loudest peak in the table, keeps the
RMS equal, so VELO changes colour and not loudness.

What is a convention rather than the sieve: equal strength for every present harmonic,
the same starting phase for all of them, and reading forward from i. The sieve supplies
presence and absence; this is the most direct way to sound it.

128 frames, because MIDI notes and velocities run 0-127: with Serum's NOTE or VELO at its
default straight line, value v sits exactly on frame v. The table repeats every P frames
(40 here) — the sieve does.

The SWEEP table follows the voice's whole parity statement: frame k is the frame for the
velocity the piece gives step k (0 at a rest), and it ends on its first frame again, so a
ramp of WT POS across the clip puts each step's timbre on its step.

Files are written as Serum 2's own wavetables are — 32-bit float, mono, 2048 samples a
frame — with a 'clm ' chunk '<!>2048 00000000 wavetable (...)': no blending between
frames, and Serum's factory flag clear, as it must be for a custom table.
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
    """d: how far apart neighbouring frames' cuts are. The lattice's diagonal, or 1.

    The diagonal belongs to the sieve the voice descends from. It must also be a unit
    modulo the voice's own period, or some cuts would never be reached; for a voice
    derived from one sieve it always is, since the voice closes on that sieve's period.
    """
    d = diagonal(ancestral_moduli(cfg, config.INSTRUMENT_CONFIGS))
    if d is None or math.gcd(d, period) != 1:
        return 1
    return d


def cut(order, period, i):
    """The harmonic below frame i's first: its register."""
    return (order * i) % period


def harmonics_for(rhythm, order, i):
    """Frame i's harmonics: the sieve read from i + 1, sounded from just above the cut."""
    period = len(rhythm)
    start = cut(order, period, i)
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
    """`Tables/<project>/<version>`: every table of the project under one folder.

    The author asked for one `sifters` folder in Serum's menu with a folder per version
    inside it (2026-10-11). Serum 2's own factory tables sit at the same depth —
    `Tables/S2 Tables/Analog/*.wav` — so Serum scans it, whatever the guide's Serum 1-era
    line about subfolders says (p. 345).
    """
    return os.path.join(presets or serum_presets_folder(), 'Tables',
                        config.SERUM_PROJECT, config.TITLE)


def installed_name(filename):
    """`dois_41_wavetable_A_sweep.wav` -> `A sweep.wav`: the folders already say the rest."""
    stem = os.path.splitext(filename)[0].removeprefix(f"{config.TITLE}_wavetable_")
    return stem.replace('_', ' ') + '.wav'


def install_into_serum(source_dir, filenames, target_dir):
    """Copy finished wavetables into Serum, so they appear in its wavetable menu.

    `target_dir` must be `Tables/<project>/<version>` — no shallower, because the author
    wants one project folder, and no deeper than Serum's own factory tables go. Only the
    given tables are written; nothing else there is touched. Called only from
    `compose.py --install-serum`, never by a plain render, so no test or ordinary run
    writes outside the project.
    """
    parts = os.path.normpath(target_dir).split(os.sep)
    if len(parts) < 3 or parts[-3] != 'Tables':
        raise ValueError(f"{target_dir} is not Tables/<project>/<version> inside a Serum "
                         f"presets folder; Serum would not list it where it belongs")
    os.makedirs(target_dir, exist_ok=True)
    copied = []
    for name in filenames:
        if name.endswith('.wav'):
            target = installed_name(name)
            shutil.copyfile(os.path.join(source_dir, name), os.path.join(target_dir, target))
            copied.append(target)
    return copied
