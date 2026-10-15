"""Serum wavetables from the sieve. dois_37 introduced them; dois_38 and dois_39 reworked them.

Two tables per voice, both read straight off the sieves:

  * the VELOCITY table — eight frames, one per accent state, in velocity order. Route
    Serum's VELO to wavetable position and each note's accents choose its sound;
  * the SWEEP table — the voice's whole parity statement, one frame per step, ending
    where it began. Ramp wavetable position across the clip and the timbre follows the
    accents through time, including the span accent's drift across the passes, which a
    single frame per state cannot show.

What a frame is, for one voice in one accent state:

  * ONE PERIOD OF THE SIEVE, AS HARMONICS. A sieve is a rule over all whole numbers; its
    period (40 for psappha, the LCM of 8 and 5) is the shortest span that says
    everything it has to say. Harmonics are whole numbers too, so harmonic h sounds if
    h is in the voice's sieve, for h = 1 .. period — the period stated exactly once, in
    frequency, as Principle I requires of duration. Extending it further would repeat
    the same period up the spectrum: padding, in the frequency domain. A rest is a
    missing partial; A and B are complements, so between them every harmonic sounds.
    (dois_37 mapped step n to harmonic n+1, an offset with no reason behind it.)
  * THE FUNDAMENTAL ALWAYS SOUNDS — the one exception. Pitch comes from the MIDI, and B
    does not contain 1, so without it B's pitch could seem to jump an octave;
  * THE ACCENTS, READ THE SAME WAY. Each accent firing in the state lifts harmonic h if
    h is in that accent's sieve, by WAVETABLE_EMPHASIS x its rarity — the rarity that
    ranks the velocity table. A rarer state, with more and rarer accents, is more
    strongly coloured. Not necessarily brighter: the harmonics an accent marks can be
    low ones;
  * partials fall off as 1/h ** WAVETABLE_ROLLOFF, and each frame is normalised on its
    own, so frames differ in colour, not level. Rolloff and emphasis are CHOICES, and
    config.py says so;
  * every partial starts IN PHASE, the same in every frame — so the positions between
    two frames are clean blends of their spectra, never smeared ones. Spreading the
    phases was tried in dois_38 and MEASURED worse: averaged over every frame, peak-to-
    average rose from 1.65 to 1.90 with Newman's phases and 1.79 with Schroeder's, which
    is 1.2 dB quieter at the same peak. Those phases suit spectra whose harmonics are
    all equally loud; a 1/h spectrum in phase is already a sawtooth's shape, about as
    smooth as such a spectrum gets.

Files are written as Serum 2's own wavetables are — 32-bit float, mono, 2048 samples a
frame — with a 'clm ' chunk reading '<!>2048 BC000000 <comment>'. B is how Serum blends
between frames (0 none, 1 crossfade, 2-4 spectral morphs) and C is the "Serum factory"
flag, which must NEVER be 1 for a custom table. dois_38 copied '11000000' from Serum's
factory files and so marked these tables as factory ones; dois_39 writes '00000000':
no blending, not factory. No blending suits both tables: each velocity, and each step of
the sweep, is one discrete accent state. (Smooth Interpolation on Serum's WT POS knob
turns blending on without changing the file.)

How Serum takes them in (Serum 2 User Guide, pp. 290-298, 345): dragging a WAV onto an
oscillator ALWAYS offers a choice of import methods — that is Serum's design, not a
fault in the file. A `.txt` beside the WAV reading `[2048]` / `[no interp]` tells Serum
the frame size on a drag; and tables placed in a folder directly inside Serum's Tables
folder appear in the oscillator's wavetable menu and load with no import step at all.
`install_into_serum` puts them there.
"""
import os
import shutil
import struct
from fractions import Fraction

import numpy as np

import config
from accents import accent_code, shared_velocity_levels
from sieve import evaluate

SAMPLE_RATE = 44100           # irrelevant to a wavetable's pitch; WAV needs one
PEAK = 0.95                   # headroom below full scale
MAX_FRAMES = 256              # Serum's limit


def serum_marker():
    """The 'clm ' text: frame size, no blending (0), NOT a factory table (0).

    The comment after the flags is free text; this is the one Serum's own exports carry,
    kept because it is known to import cleanly.
    """
    return f"<!>{config.WAVETABLE_FRAME_SAMPLES} 00000000 wavetable (www.xferrecords.com)"


def sidecar_text():
    """What Serum reads from `name.txt` beside a dragged `name.wav` (User Guide p. 295)."""
    return f"[{config.WAVETABLE_FRAME_SAMPLES}]\n[no interp]\n"


def accent_weights(fields):
    """Each accent's rarity in bit order — the same numbers the velocity table uses."""
    rarity = lambda arr: Fraction(len(arr) - int(arr.sum()), len(arr))
    names = list(fields)
    labels = list(fields[names[0]]['accents'])
    weights = [rarity(fields[names[0]]['accents'][label]) for label in labels[:-1]]
    weights.append(max(rarity(f['accents'][list(f['accents'])[-1]]) for f in fields.values()))
    return weights


def phases(harmonics):
    """Every partial in phase, identical in every frame — measured best; see above."""
    return np.zeros(harmonics)


def spectrum(rhythm, accent_expressions, weights, code):
    """Harmonic amplitudes 1 .. period for one voice in one accent state."""
    period = len(rhythm)
    h = np.arange(1, period + 1)
    present = np.array([rhythm[k % period] for k in h], dtype=float)
    present[0] = 1.0                                     # the fundamental always sounds
    emphasis = np.ones(period)
    for bit, (expression, weight) in enumerate(zip(accent_expressions, weights)):
        if code >> bit & 1:
            marks = np.asarray(evaluate(expression, period + 1), dtype=float)[1:]
            emphasis += config.WAVETABLE_EMPHASIS * float(weight) * marks
    return present * emphasis / h ** config.WAVETABLE_ROLLOFF


def synthesise(amplitudes):
    """One single cycle from harmonic amplitudes, normalised to PEAK."""
    samples = config.WAVETABLE_FRAME_SAMPLES
    t = 2 * np.pi * np.arange(samples) / samples
    phi = phases(len(amplitudes))
    frame = sum(a * np.sin(h * t + phi[h - 1])
                for h, a in enumerate(amplitudes, start=1) if a)
    return PEAK * frame / np.max(np.abs(frame))


def velocity_frames(state_frame, levels):
    """Eight frames, one per accent state, from the lowest velocity to the highest.

    With Serum's VELO at its default straight line, velocity v sits v/127 of the way
    through the table, and each of this piece's velocities lands within a twentieth of a
    frame of its own: 1 -> 0.06, 19 -> 1.05 ... 109 -> 6.01, 127 -> 7. With blending off,
    Serum plays the frame it lands on. dois_38 gave each state a band of 16 identical
    frames to make that exact, which showed in Serum as 128 frames of which only 8
    differed — and Serum's own guidance (p. 346) favours few, distinct frames. If a
    velocity ever lands one frame off, reshape the modulation's curve in Serum's matrix.
    """
    ordered = sorted(levels.items(), key=lambda item: (item[1], item[0]))
    return [state_frame[code] for code, _ in ordered]


def sweep_frames(state_frame, field):
    """The voice's whole parity statement: one frame per step, closing on the first.

    `span` steps, then step 0 again, so a ramp of wavetable position from 0 to 1 across
    the clip puts step k exactly at k / span — the cycle closes where it started.
    Returns None when the statement is longer than Serum's 256 frames allow.
    """
    labels = list(field['accents'])
    span = field['span']
    if span + 1 > MAX_FRAMES:
        return None
    codes = accent_code(field['accents'], labels, span)
    return [state_frame[int(code)] for code in codes] + [state_frame[int(codes[0])]]


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


def write_wavetables(fields, base_binaries, prefix, directory):
    """Every voice's tables. Returns the file names written."""
    weights = accent_weights(fields)
    levels = shared_velocity_levels({n: f['accents'] for n, f in fields.items()})
    written = []
    for name, field in fields.items():
        rhythm = base_binaries[name]
        if len(rhythm) > config.WAVETABLE_FRAME_SAMPLES // 2 - 1:
            raise ValueError(f"{name}'s {len(rhythm)}-step period needs that many "
                             f"harmonics, more than a {config.WAVETABLE_FRAME_SAMPLES}-"
                             f"sample frame holds without aliasing")
        expressions = list(field['accent_dict'].values())
        state_frame = {code: synthesise(spectrum(rhythm, expressions, weights, code))
                       for code in levels}

        filename = f"{prefix}_wavetable_{name}_velocity.wav"
        frames = velocity_frames(state_frame, levels)
        write_wav(os.path.join(directory, filename), frames)
        written += [filename, write_sidecar(directory, filename)]
        print(f"  Saved: {filename}  ({len(frames)} frames, one per accent state in velocity "
              f"order; {len(rhythm)} harmonics, one period of the sieve)")

        if config.WAVETABLE_SWEEP:
            frames = sweep_frames(state_frame, field)
            if frames is None:
                print(f"  -- {name}: no sweep table; its {field['span']}-step statement "
                      f"needs {field['span'] + 1} frames, Serum allows {MAX_FRAMES}")
                continue
            filename = f"{prefix}_wavetable_{name}_sweep.wav"
            write_wav(os.path.join(directory, filename), frames)
            written += [filename, write_sidecar(directory, filename)]
            print(f"  Saved: {filename}  ({len(frames)} frames — the {field['span']}-step "
                  f"statement, closing on its first step)")
    return written


def write_sidecar(directory, wav_name):
    """`name.txt` beside `name.wav`, so a drag-and-drop import knows the frame size."""
    name = os.path.splitext(wav_name)[0] + '.txt'
    with open(os.path.join(directory, name), 'w') as handle:
        handle.write(sidecar_text())
    return name


def install_into_serum(source_dir, filenames, target_dir):
    """Copy finished wavetables into Serum's Tables folder, so they appear in its menu.

    `target_dir` must sit DIRECTLY inside Serum's `Tables` folder: Serum does not scan
    deeper (User Guide p. 345). Only the given files are written; nothing else there is
    touched. Called only from `compose.py --install-serum`, never by a plain render, so
    no test or ordinary run writes outside the project.
    """
    tables = os.path.dirname(os.path.normpath(target_dir))
    if os.path.basename(tables) != 'Tables':
        raise ValueError(f"{target_dir} is not directly inside a Serum 'Tables' folder; "
                         f"Serum would not find tables there")
    os.makedirs(target_dir, exist_ok=True)
    copied = []
    for name in filenames:
        if name.endswith('.wav'):
            shutil.copyfile(os.path.join(source_dir, name), os.path.join(target_dir, name))
            copied.append(name)
    return copied
