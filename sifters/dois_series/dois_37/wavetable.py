"""Serum wavetables from the sieve: one frame per accent state, in velocity order.

The MIDI already carries the piece's accent structure as velocity — eight states, eight
velocities, one table shared by every voice. A wavetable with one frame per state, in
that same order, lets a synthesizer turn each velocity into a TIMBRE: route velocity to
wavetable position and the accents choose the sound instead of the loudness. Nothing in
the MIDI changes; the wavetable is a second rendering of the same derivation.

How a frame is built, for one voice and one accent state:

  * the spectrum is the voice's own rhythm. Step n of its note layer sets harmonic n+1,
    so the layer's period is the number of harmonics and every rest is a missing
    partial. A and B are complements, so their timbres are too — together they hold
    every harmonic. The one exception is the fundamental, which always sounds: the
    note's pitch comes from the MIDI, and a rhythm that rests on step 0 would otherwise
    leave the pitch ambiguous;
  * partials fall off as 1/h, the way a sawtooth's do;
  * each accent firing in that state EMPHASISES the harmonics whose steps it marks, in
    proportion to its rarity — the same rarity that ranks the velocity table. A rarer
    state has more, and rarer, accents firing, so it is the most strongly coloured;
  * the frame is normalised on its own, so frames differ in colour, not level.

The span accent's period need not divide the layer (that is what lets it move across
passes), so for the spectrum it is read over the layer's first statement only.
"""
import os
import struct
from fractions import Fraction

import numpy as np

import config
from accents import shared_velocity_levels
from sieve import evaluate

SAMPLE_RATE = 44100           # irrelevant to a wavetable's pitch; WAV needs one
PEAK = 0.95                   # headroom below full scale


def state_order(levels):
    """Accent states from quietest velocity to loudest — one frame each, in this order.

    With velocities spaced evenly from MIN to MAX, velocity v sits at (v - MIN) / range
    of the way through the table, which is exactly where frame k of n sits when a
    synthesizer maps velocity to wavetable position. So frame k IS velocity level k.
    """
    return [code for code, _ in sorted(levels.items(), key=lambda item: (item[1], item[0]))]


def accent_weights(fields):
    """The rarity of each accent, in bit order — the same numbers the velocity table uses."""
    rarity = lambda arr: Fraction(len(arr) - int(arr.sum()), len(arr))
    names = list(fields)
    labels = list(fields[names[0]]['accents'])
    weights = [rarity(fields[names[0]]['accents'][label]) for label in labels[:-1]]
    weights.append(max(rarity(f['accents'][list(f['accents'])[-1]]) for f in fields.values()))
    return weights


def frame_spectrum(rhythm, accents_over_layer, weights, code):
    """Harmonic amplitudes 1..len(rhythm) for one voice in one accent state."""
    harmonics = np.arange(1, len(rhythm) + 1)
    present = rhythm.astype(float).copy()
    present[0] = 1.0                                    # the fundamental always sounds
    emphasis = np.ones(len(rhythm))
    for bit, (marks, weight) in enumerate(zip(accents_over_layer, weights)):
        if code >> bit & 1:
            emphasis += config.WAVETABLE_EMPHASIS * float(weight) * marks
    return present * emphasis / harmonics


def synthesise(amplitudes, samples):
    """One single-cycle frame from harmonic amplitudes, normalised to PEAK."""
    phase = 2 * np.pi * np.arange(samples) / samples
    frame = np.zeros(samples)
    for h, amplitude in enumerate(amplitudes, start=1):
        if amplitude:
            frame += amplitude * np.sin(h * phase)
    return PEAK * frame / np.max(np.abs(frame))


def voice_frames(field, rhythm, weights, order):
    """Every frame for one voice, in velocity order."""
    layer = len(rhythm)
    samples = config.WAVETABLE_FRAME_SAMPLES
    if layer > samples // 2 - 1:
        raise ValueError(f"a {layer}-step layer needs {layer} harmonics, more than a "
                         f"{samples}-sample frame can hold without aliasing")
    accents = [np.asarray(field['accents'][label][:layer], dtype=float)
               for label in field['accents']]
    return [synthesise(frame_spectrum(rhythm, accents, weights, code), samples)
            for code in order]


def write_wav(path, frames):
    """24-bit mono WAV, frames back to back, with Serum's frame-size marker.

    Serum reads a 'clm ' chunk whose text begins '<!>' plus the frame size to know how
    to cut a file into frames. Without it, Serum asks how to import and 2048-sample
    frames can be chosen by hand. The flags after the size are written as zeros.
    """
    audio = np.concatenate(frames)
    pcm = np.round(audio * (2 ** 23 - 1)).astype('<i4')
    data = b''.join(int(x).to_bytes(3, 'little', signed=True) for x in pcm)
    marker = f"<!>{config.WAVETABLE_FRAME_SAMPLES} 00000000 wavetable (sifters)".encode()
    if len(marker) % 2:
        marker += b'\0'
    fmt = struct.pack('<HHIIHH', 1, 1, SAMPLE_RATE, SAMPLE_RATE * 3, 3, 24)
    chunks = (b'fmt ' + struct.pack('<I', len(fmt)) + fmt
              + b'clm ' + struct.pack('<I', len(marker)) + marker
              + b'data' + struct.pack('<I', len(data)) + data)
    with open(path, 'wb') as handle:
        handle.write(b'RIFF' + struct.pack('<I', 4 + len(chunks)) + b'WAVE' + chunks)


def read_wav(path):
    """Frames back out of a file written by `write_wav`, by parsing it independently."""
    with open(path, 'rb') as handle:
        blob = handle.read()
    assert blob[:4] == b'RIFF' and blob[8:12] == b'WAVE', 'not a RIFF WAVE file'
    chunks, at = {}, 12
    while at < len(blob):
        tag, size = blob[at:at + 4], struct.unpack('<I', blob[at + 4:at + 8])[0]
        chunks[tag] = blob[at + 8:at + 8 + size]
        at += 8 + size + (size % 2)
    channels, rate, bits = (struct.unpack('<H', chunks[b'fmt '][2:4])[0],
                            struct.unpack('<I', chunks[b'fmt '][4:8])[0],
                            struct.unpack('<H', chunks[b'fmt '][14:16])[0])
    raw = chunks[b'data']
    values = np.array([int.from_bytes(raw[i:i + 3], 'little', signed=True)
                       for i in range(0, len(raw), 3)]) / (2 ** 23 - 1)
    marker = chunks.get(b'clm ', b'').rstrip(b'\0').decode()
    return values, {'channels': channels, 'rate': rate, 'bits': bits, 'marker': marker}


def write_wavetables(fields, base_binaries, prefix, directory):
    """One file per voice. Returns the file names written."""
    weights = accent_weights(fields)
    # The order comes from the very function that gave the MIDI its velocities, so the
    # frames cannot drift out of step with the notes that select them.
    order = state_order(shared_velocity_levels({n: f['accents'] for n, f in fields.items()}))
    written = []
    for name, field in fields.items():
        frames = voice_frames(field, base_binaries[name], weights, order)
        filename = f"{prefix}_wavetable_{name}.wav"
        write_wav(os.path.join(directory, filename), frames)
        written.append(filename)
        print(f"  Saved: {filename}  ({len(frames)} frames x "
              f"{config.WAVETABLE_FRAME_SAMPLES} samples, {len(base_binaries[name])} "
              f"harmonics, {int(base_binaries[name].sum())} from the rhythm)")
    return written
