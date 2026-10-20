"""The lattice's period as an octave: tuning files for the pitched modes.

The lattice puts 40 pitches on MIDI 36-75, one per step of the sieve's period. Tuned so
that the PERIOD is the octave, each step is 1200/40 = 30 cents, and the lattice's own
moves land near simple ratios:

    one step of the sieve, x13 ......... 390 cents   (5/4, a major third, is 386)
    the canon's displacement, +9 ....... 270 cents   (7/6 is 267)
    C against A in canon mode, 31 ...... 930 cents   (12/7 is 933)

The one choice is that the period spans an octave. The root keeps its usual pitch (MIDI
36, 65.41 Hz), so tuned and untuned files start in the same place.

  * `<title>_tuning.tun`: AnaMark TUN, loaded per Serum instance (Global > TUN FILE >
    Load Tuning; User Guide p. 320). Serum keeps it in the preset: verified, notes land
    exactly 30 cents apart.
  * `<title>_tuning.scl` and `.kbm`: a Scala scale and keyboard map, for MTS-ESP MINI,
    which retunes every instance at once (p. 321).
"""
import os

import config
from pitch import lattice_axes

CENTS_REFERENCE_HZ = 8.1757989156437073336     # MIDI note 0 in 12-tone equal temperament


def tuning_period():
    """Steps per octave: the lattice's period, the product of the sieve's two moduli."""
    row, col = lattice_axes()
    return row * col


def cents_above_note_zero(note, period=None):
    """Where a MIDI note sits once the period spans an octave, anchored at the root."""
    period = period or tuning_period()
    return 100 * config.PITCH_ROOT + (note - config.PITCH_ROOT) * 1200 / period


def root_hz():
    return CENTS_REFERENCE_HZ * 2 ** (config.PITCH_ROOT / 12)


def tun_text(title):
    period = tuning_period()
    lines = [f"; {title}: the sieve's {period}-step period as one octave",
             "; Written by sifters. Every MIDI note, as cents above 8.1758 Hz.",
             "",
             "[Tuning]"]
    lines += [f"note {n}={round(cents_above_note_zero(n, period))}" for n in range(128)]
    lines += ["", "[Exact Tuning]", f"BaseFreq={CENTS_REFERENCE_HZ:.16f}"]
    lines += [f"note {n}={cents_above_note_zero(n, period):.6f}" for n in range(128)]
    return "\n".join(lines) + "\n"


def scl_text(title):
    period = tuning_period()
    lines = [f"! {title}_tuning.scl",
             "!",
             f"{period} equal steps to the octave: the sieve's period as one octave",
             f" {period}",
             "!"]
    lines += [f" {step * 1200 / period:.6f}" for step in range(1, period)]
    lines += [" 2/1"]
    return "\n".join(lines) + "\n"


def kbm_text(title):
    period = tuning_period()
    return "\n".join([
        f"! {title}_tuning.kbm",
        "! Size of map (0: every key is the next scale degree):",
        "0",
        "! First MIDI note number to retune:",
        "0",
        "! Last MIDI note number to retune:",
        "127",
        "! Middle note where the first entry of the mapping is mapped to:",
        str(config.PITCH_ROOT),
        "! Reference note for which frequency is given:",
        str(config.PITCH_ROOT),
        "! Frequency to tune the above note to:",
        f"{root_hz():.6f}",
        "! Scale degree to consider as formal octave:",
        str(period),
        "! Mapping.",
    ]) + "\n"


def write_tuning(title, directory):
    """The three tuning files. Returns their names."""
    written = []
    for suffix, text in (('tun', tun_text(title)), ('scl', scl_text(title)),
                         ('kbm', kbm_text(title))):
        name = f"{title}_tuning.{suffix}"
        with open(os.path.join(directory, name), 'w') as handle:
            handle.write(text)
        written.append(name)
    print(f"  Saved: {', '.join(written)}  ({tuning_period()} steps to the octave, "
          f"MIDI {config.PITCH_ROOT} at {root_hz():.2f} Hz)")
    return written
