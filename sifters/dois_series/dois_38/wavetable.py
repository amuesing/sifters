"""Serum wavetables from the sieve. dois_37 introduced them; dois_38 reworked them.

Two tables per voice, both read straight off the sieves:

  * the VELOCITY table — the timbre of each accent state, selected by velocity. Route
    velocity to wavetable position in Serum and each note's accents choose its sound;
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

Files are written exactly as Serum 2's own factory wavetables are: 32-bit float, mono,
with a 'clm ' chunk reading '<!>2048 11000000 wavetable (www.xferrecords.com)'. Read
from the 288 tables Serum 2 installs; dois_37's zeros in place of the flags made Serum
ask for the frame size.
"""
import os
import struct
from fractions import Fraction

import numpy as np

import config
from accents import accent_code, shared_velocity_levels
from sieve import evaluate

SAMPLE_RATE = 44100           # irrelevant to a wavetable's pitch; WAV needs one
PEAK = 0.95                   # headroom below full scale
MAX_FRAMES = 256              # Serum's limit
VELOCITY_FRAMES = 128         # one per MIDI velocity, 0..127


def serum_marker():
    """The text Serum 2 writes into its own wavetables, with this frame size."""
    return f"<!>{config.WAVETABLE_FRAME_SAMPLES} 11000000 wavetable (www.xferrecords.com)"


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


def nearest_level(velocity, levels_in_order):
    """The state whose velocity is closest; a tie goes to the lower one."""
    return min(levels_in_order, key=lambda item: (abs(item[1] - velocity), item[1]))[0]


def velocity_frames(state_frame, levels):
    """128 frames, frame v sounding the state whose velocity is nearest v.

    Serum reads a velocity as v/127 of the way through the table, and frame k of 128
    sits at k/127 — so velocity v lands EXACTLY on frame v. Each of the eight timbres
    fills the band of velocities nearest it, so a mapping that is slightly off still
    lands inside the right timbre. (dois_37 used eight frames, where the lowest level
    sat about 5% of a frame away from its own.)
    """
    ordered = sorted(levels.items(), key=lambda item: (item[1], item[0]))
    return [state_frame[nearest_level(v, ordered)] for v in range(VELOCITY_FRAMES)]


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
        write_wav(os.path.join(directory, filename), velocity_frames(state_frame, levels))
        written.append(filename)
        print(f"  Saved: {filename}  ({VELOCITY_FRAMES} frames — 8 timbres, one band per "
              f"velocity level; {len(rhythm)} harmonics, one period of the sieve)")

        if config.WAVETABLE_SWEEP:
            frames = sweep_frames(state_frame, field)
            if frames is None:
                print(f"  -- {name}: no sweep table; its {field['span']}-step statement "
                      f"needs {field['span'] + 1} frames, Serum allows {MAX_FRAMES}")
                continue
            filename = f"{prefix}_wavetable_{name}_sweep.wav"
            write_wav(os.path.join(directory, filename), frames)
            written.append(filename)
            print(f"  Saved: {filename}  ({len(frames)} frames — the {field['span']}-step "
                  f"statement, closing on its first step)")
    return written
