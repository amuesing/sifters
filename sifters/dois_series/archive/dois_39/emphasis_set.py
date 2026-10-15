"""A listening set: the velocity tables at several emphasis strengths. dois_39.

`WAVETABLE_EMPHASIS` — how strongly a firing accent lifts the harmonics in its sieve — is
a choice, not a derivation, and the closest pair of states differs on only a few
harmonics, so how much contrast the eight timbres should have is a question for the ear.
This writes each voice's velocity table at each strength into `listening/`, and reports
how different the most similar pair of timbres comes out at each.

    python3 emphasis_set.py                   # write listening/ and report
    python3 emphasis_set.py --install-serum   # and copy them into Serum's menu as well

Nothing about the piece changes. The render (`compose.py`) keeps using config.py's value.
"""
import contextlib
import io
import math
import os
import sys

import numpy as np

import config
import compose
from accents import derive_weather, shared_velocity_levels
from wavetable import (accent_weights, install_into_serum, spectrum, synthesise,
                       velocity_frames, write_sidecar, write_wav)

STRENGTHS = (3.0, 8.0, 20.0)
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'listening')


def derived_fields():
    """The piece's accents, derived exactly as a render derives them."""
    with contextlib.redirect_stdout(io.StringIO()):
        base, layers = compose.derive_note_layers()
        units = {c['name']: compose.get_step_ticks(c) for c in config.INSTRUMENT_CONFIGS}
        parity = compose.parity_point(layers, units)
    passes = {n: parity // (layers[n] * units[n]) for n in layers}
    first = config.INSTRUMENT_CONFIGS[0]
    weather = config.WEATHER or derive_weather(base, first['sieve'], layers, passes=passes)
    source = config.SPAN_RESIDUE_SOURCE
    fields = {c['name']: compose.accent_field(c, base, layers, units, parity, weather,
                                              source, quiet=True)
              for c in config.INSTRUMENT_CONFIGS}
    return base, fields


def closest_pair(frames, harmonics):
    """The two most similar timbres: their mean dB difference, and their largest.

    Both, because they tell different stories. The closest pair differs only by the
    span accent, whose sieve marks a handful of the harmonics, so the MEAN stays small
    however strong the emphasis — but those few harmonics move a lot, which the ear
    hears as a peak appearing in the tone rather than a change of its whole colour.
    """
    spectra = np.abs(np.fft.rfft(np.array(frames), axis=1))[:, 1:harmonics + 1]
    spectra /= spectra.max(axis=1, keepdims=True)
    sounding = spectra.max(axis=0) > 1e-3
    db = 20 * np.log10(np.maximum(spectra[:, sounding], 1e-9))
    mean, i, j = min((np.mean(np.abs(db[i] - db[j])), i, j)
                     for i in range(len(frames)) for j in range(i + 1, len(frames)))
    return mean, np.abs(db[i] - db[j]).max()


def main():
    os.makedirs(OUT, exist_ok=True)
    base, fields = derived_fields()
    weights = accent_weights(fields)
    levels = shared_velocity_levels({n: f['accents'] for n, f in fields.items()})
    written = []
    print(f"Velocity tables at {len(STRENGTHS)} emphasis strengths -> listening/\n")
    print("  the most similar pair of timbres: mean dB difference / its largest single")
    print("  harmonic change (around 1 dB is barely audible; 6 dB is clearly heard):\n")
    print("  voice  " + "  ".join(f"emphasis {e:>4g}  " for e in STRENGTHS))
    for name, field in fields.items():
        row = []
        for emphasis in STRENGTHS:
            config.WAVETABLE_EMPHASIS = emphasis
            expressions = list(field['accent_dict'].values())
            state_frame = {code: synthesise(spectrum(base[name], expressions, weights, code))
                           for code in levels}
            frames = velocity_frames(state_frame, levels)
            filename = f"{config.TITLE}_{name}_velocity_emphasis{emphasis:02.0f}.wav"
            write_wav(os.path.join(OUT, filename), frames)
            write_sidecar(OUT, filename)
            written.append(filename)
            row.append(closest_pair(frames, len(base[name])))
        print(f"    {name}    " + "  ".join(f"{m:>5.1f} / {x:>4.1f} dB" for m, x in row))
    if '--install-serum' in sys.argv:
        copied = install_into_serum(OUT, written, config.SERUM_TABLES_DIR)
        print(f"\n  {len(copied)} installed in Serum: {config.SERUM_TABLES_DIR}")


if __name__ == '__main__':
    main()
