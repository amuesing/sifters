"""Audio previews: a quick way to HEAR a study without opening Ableton or Serum.

These are sketches, not renders of your patches. Two ways of sounding a MIDI file:

  * `wavetable_voice` plays a sifters wavetable the way Serum does with pitch tracking
    off: a fixed pitch per voice, and the note number (NOTE -> WT POS) or the velocity
    (VELO -> WT POS) choosing the frame. Each frame is band-limited to the playback
    pitch first, as Serum's own oscillator is, so nothing folds back above 22 kHz;
  * `tone_voice` plays pitch: a plucked tone with eight harmonics, in 12-tone equal
    temperament or in the 40-step tuning that makes the sieve's period an octave.

Choices that belong to the preview and not to the piece: the fixed pitches, the
envelopes, the plucked timbre, velocity to loudness where it is used, and transposing
pitched previews up so the lattice's bass register is audible on small speakers.
"""
import struct

import mido
import numpy as np

SR = 44100
ATTACK, RELEASE = 0.003, 0.04


def midi_events(path):
    """[(seconds on, seconds long, note, velocity, track)] for every note in the file."""
    mid = mido.MidiFile(path)
    seconds_per_tick = 0.5 / mid.ticks_per_beat            # 120 BPM, as the piece states
    events = []
    for track_index, track in enumerate(mid.tracks):
        t, sounding = 0, {}
        for msg in track:
            t += msg.time
            key = (getattr(msg, 'channel', 0), getattr(msg, 'note', None))
            if msg.type == 'note_on' and msg.velocity:
                sounding[key] = (t, msg.velocity)
            elif msg.type in ('note_off', 'note_on') and key in sounding:
                on, velocity = sounding.pop(key)
                events.append((on * seconds_per_tick, (t - on) * seconds_per_tick,
                               msg.note, velocity, track_index))
    return events


def length_of(path):
    mid = mido.MidiFile(path)
    return max(sum(m.time for m in tr) for tr in mid.tracks) * 0.5 / mid.ticks_per_beat


def envelope(n, held):
    """Attack, hold until the note ends, then release."""
    t = np.arange(n) / SR
    env = np.minimum(1.0, t / ATTACK)
    after = t > held
    env[after] *= np.exp(-(t[after] - held) / (RELEASE / 4))
    return env


def band_limited(frame, f0):
    """Remove every harmonic that would sound above 20 kHz at this pitch."""
    spectrum = np.fft.rfft(frame)
    top = int(20000 // f0)
    spectrum[top + 1:] = 0
    return np.fft.irfft(spectrum, len(frame))


def wavetable_voice(events, table, f0, frame_of, loudness_of, total):
    """A sifters table at a fixed pitch; `frame_of(note, velocity)` picks the frame."""
    out = np.zeros(int(total * SR) + SR)
    cache = {}
    size = table.shape[1]
    for on, held, note, velocity, _ in events:
        index = frame_of(note, velocity)
        if index not in cache:
            cache[index] = band_limited(table[index], f0)
        frame = cache[index]
        n = int((held + RELEASE) * SR)
        phase = (np.arange(n) * f0 / SR * size) % size
        low = phase.astype(int)
        frac = phase - low
        wave = frame[low] * (1 - frac) + frame[(low + 1) % size] * frac
        start = int(on * SR)
        out[start:start + n] += loudness_of(velocity) * envelope(n, held) * wave
    return out[:int(total * SR)]


def tone_voice(events, hz_of, loudness_of, total, brightness=1.0):
    """A plucked tone at each note's pitch: eight harmonics, the upper ones dying first."""
    out = np.zeros(int(total * SR) + 2 * SR)
    for on, held, note, velocity, _ in events:
        hz = hz_of(note)
        ring = max(held, 0.18)
        n = int((ring + 0.25) * SR)
        t = np.arange(n) / SR
        wave = np.zeros(n)
        for h in range(1, 9):
            if h * hz > 18000:
                break
            wave += np.sin(2 * np.pi * h * hz * t) * np.exp(-t * (2.5 + 3.0 * h / brightness)) / h
        start = int(on * SR)
        out[start:start + n] += loudness_of(velocity) * np.minimum(1.0, t / ATTACK) * wave
    return out[:int(total * SR) + SR]


def twelve_tet(shift=0):
    return lambda note: 440.0 * 2 ** ((note + shift - 69) / 12)


def forty_step(root_note=36, root_hz=261.63):
    """The sieve's period as an octave (dois_43's tuning), root moved up for audibility."""
    return lambda note: root_hz * 2 ** ((note - root_note) / 40)


LOUDNESS = 0.075          # RMS every preview is set to, so comparisons are at equal loudness


def write_wav(path, signal):
    """16-bit mono WAV at one RMS for every preview, the peak kept below full scale.

    Normalising each file to its own peak made a dense table sound twice as loud as a
    sparse one, which would bias every comparison; equal RMS does not.
    """
    rms = np.sqrt(np.mean(signal ** 2)) or 1.0
    peak = np.max(np.abs(signal)) or 1.0
    gain = min(LOUDNESS / rms, 0.98 / peak)
    data = (np.clip(signal * gain, -1, 1) * 32767).astype('<i2').tobytes()
    header = (b'RIFF' + struct.pack('<I', 36 + len(data)) + b'WAVE'
              + b'fmt ' + struct.pack('<IHHIIHH', 16, 1, 1, SR, SR * 2, 2, 16)
              + b'data' + struct.pack('<I', len(data)))
    with open(path, 'wb') as handle:
        handle.write(header + data)
