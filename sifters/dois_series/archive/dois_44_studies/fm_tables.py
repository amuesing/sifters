"""Baked FM: a table per voice whose frame number is the modulation depth.

Frame k is a sine carrier phase-modulated by the voice's own frame 0, 1:1, at depth
I_max x k / 127: frame 0 is a pure sine, frame 127 the voice's sieve at its deepest as FM
sidebands. Played with an envelope on WT POS, a stroke starts deep in the table and
settles into the sine.

I_max is derived, not chosen: the deepest modulation that keeps 99.9% of every frame's
energy within two periods of harmonics (2P - 1, harmonic 79 for psappha), the bound every
sifters table keeps so that none aliases where the others do not. Found by bisection,
then checked on every frame: 2.2-2.35 rad for psappha's voices.

Why a sine carrier: with the voice's whole frame as carrier and its complement as
modulator, as the live FM pairs do, the frame's harmonics already fill half the band, and
the same bound allows only 0.03 rad (0.04-0.16 even at each drum's own Nyquist limit):
no FM at all. Serum computes live FM at audio rate and has no such ceiling, which is
why the live pairs can go so much further. Only integer ratios can be baked into one
cycle, so these tables are 1:1.
"""
import numpy as np

import wavetable                    # dois_44's, through percussion's path

SAMPLES = 2048
KEEP = 0.999                        # share of energy that must stay within two periods


def phase_wave(harmonics, theta):
    return sum(np.sin(h * theta) for h in harmonics)


def pm_frame(carrier, modulator, depth):
    """Every carrier harmonic, its phase pushed by the modulator (peak 1) times depth."""
    theta = 2 * np.pi * np.arange(SAMPLES) / SAMPLES
    m = phase_wave(modulator, theta)
    m = m / np.max(np.abs(m))
    return phase_wave(carrier, theta + depth * m)


def kept(frame, limit):
    """The share of a frame's energy in harmonics 1 .. limit."""
    power = np.abs(np.fft.rfft(frame)) ** 2
    return power[1:limit + 1].sum() / power[1:].sum()


def deepest(carrier, modulator, limit, hi=20.0):
    """The largest depth whose frame keeps KEEP of its energy within `limit` harmonics."""
    lo = 0.0
    for _ in range(40):
        mid = (lo + hi) / 2
        if kept(pm_frame(carrier, modulator, mid), limit) >= KEEP:
            lo = mid
        else:
            hi = mid
    return lo


def depth_table(rhythm, order):
    """(frames, I_max): 128 frames from a sine to the deepest the two-period bound allows."""
    period = len(rhythm)
    limit = 2 * period - 1
    carrier = [1]
    modulator = wavetable.harmonics_for(rhythm, order, 0)
    i_max = deepest(carrier, modulator, limit)
    frames = [pm_frame(carrier, modulator, i_max * k / 127) for k in range(128)]
    worst = min(kept(frame, limit) for frame in frames)
    if worst < KEEP:
        raise ValueError(f"a frame keeps only {worst:.4f} of its energy within {limit} "
                         f"harmonics; the bisection's depth is not safe for every frame")
    gain = wavetable.PEAK / max(np.max(np.abs(f)) for f in frames)
    return [gain * f for f in frames], i_max
