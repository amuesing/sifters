"""Run the composition: config -> voices -> MIDI files -> checks.

Read this file first. It is the whole process in order, and every step it takes is a
call into one of the four modules beside it:

    config.py    the composition itself — the sieve, the voices, the weather, tempo
    sieve.py     the sieve expression becomes a pattern; voices are derived from it
    accents.py   the weather and span accent decide each note's velocity
    midi.py      steps become timed events and get written to .mid files
    check.py     the files are read back and tested against what was intended

Nothing here knows anything about THIS sieve. Change the sieve in config.py and every
period, span, accent modulus and meter below is recomputed from it.

    python3 compose.py                 render and verify
    python3 compose.py --suggest-span  for a new sieve: residues that inflect every pass
"""
import hashlib
import itertools
import importlib.metadata
import json
import math
import os
import sys

import mido
import numpy as np

from config import *
from sieve import build_binary, true_period, voice_rhythm
from accents import (accent_voicing, create_accent_binaries, duplicate_passes,
                     shared_velocity_levels, span_accent, velocity_profile,
                     voice_span)
from midi import (clear_our_outputs, get_step_ticks, make_track, meter_for,
                  meter_for_voice, save_tracks, shared_meter, voice_events)
from check import verify
from pitch import MODES


def config_fingerprint():
    """A short hash of everything that determines the output.

    Two renders with different sieves, accents, units, tempo or meter get different
    fingerprints; two renders of the same configuration get the same one. Without it,
    files from different versions are indistinguishable once they are sitting in a
    project folder.

    dois_15's version hashed a hand-written list of settings, and when pitch was added
    the list was not updated: dois_14 and dois_15 both stamped cfg=3a412cb1 despite
    different pitches, and GATE_RATIO had never been covered at all. Any explicit list
    has that failure mode — the next setting added has to be remembered. So nothing
    here is listed by hand:

      * EVERY upper-case setting in config.py is collected automatically, so a new
        setting cannot be left out. OUTPUT_DIR is excluded — it is a path on this
        machine and would give the same music a different stamp on another one.
        'accent_dict' is excluded from the voices: main() writes it at run time,
        derived from settings that are already hashed.
      * EVERY .py file beside this one is hashed, so a change to the code — not only
        to the configuration — changes the stamp, and adding a module cannot be
        forgotten the way a hand-written list of filenames can;
      * the versions of the three libraries that shape the bytes are included.

    The trade-off is deliberate: an edit that changes nothing audible, a comment say,
    also changes the stamp. A spurious difference is harmless; a spurious match —
    two different pieces claiming one fingerprint — is the failure this exists to stop.
    """
    import config as _config
    settings = {}
    for key, value in sorted(vars(_config).items()):
        if not key.isupper() or key == 'OUTPUT_DIR':
            continue
        if key == 'INSTRUMENT_CONFIGS':
            value = [{k: v for k, v in c.items() if k != 'accent_dict'} for c in value]
        settings[key] = value
    here = os.path.dirname(os.path.abspath(__file__))
    source = {name: hashlib.sha256(open(os.path.join(here, name), 'rb').read()).hexdigest()
              for name in sorted(os.listdir(here)) if name.endswith('.py')}
    libraries = {name: importlib.metadata.version(name)
                 for name in ('mido', 'music21', 'numpy')}
    document = json.dumps({'settings': settings, 'source': source,
                           'libraries': libraries}, sort_keys=True, default=repr)
    return hashlib.sha256(document.encode()).hexdigest()[:8]


def search_residue_source(accent_field, note_layers, largest=16, most=5):
    """Find a SPAN_RESIDUE_SOURCE whose accents inflect every pass of every voice.

    Used only to make a failure actionable: when the configured residues leave passes
    identical, the error names a set that would not. It reports; it never decides.
    """
    for size in range(2, most + 1):
        for candidate in itertools.combinations(range(largest), size):
            try:
                fields = {c['name']: accent_field(c, candidate) for c in INSTRUMENT_CONFIGS}
                levels = shared_velocity_levels(
                    {n: f['accents'] for n, f in fields.items()})
                if all(not duplicate_passes(
                        accent_field(cfg, candidate, levels)['velocities'],
                        note_layers[cfg['name']]) for cfg in INSTRUMENT_CONFIGS):
                    return candidate
            except ValueError:
                continue
    return None


def derive_note_layers():
    """Every voice's pattern, and the period each one actually closes on.

    Measured, never declared. They coincide for this composition because all four
    descend from one sieve, but nothing assumes it: an independent sieve of another
    period, or a derivation that closes sooner than its sources, carries its own.
    """
    base_binaries, note_layers = {}, {}
    for cfg in INSTRUMENT_CONFIGS:
        binary, period = build_binary(cfg, base_binaries)
        base_binaries[cfg['name']] = binary
        note_layers[cfg['name']] = period

    distinct = sorted(set(note_layers.values()))
    print("Note layers (each derived from that voice's own sieve): "
          + ", ".join(f"{n} {p}" for n, p in note_layers.items())
          + (f"  — all {distinct[0]} steps\n" if len(distinct) == 1
             else f"  — {len(distinct)} different periods in play\n"))
    print("Densities:")
    for cfg in INSTRUMENT_CONFIGS:
        b = base_binaries[cfg['name']]
        print(f"  {cfg['name']}: {b.sum()}/{len(b)} steps ({100 * b.mean():.1f}%)")
    return base_binaries, note_layers


def parity_point(note_layers, units):
    """P — the first tick at which every voice has finished a whole number of layers.

    Nothing chooses it: it is the LCM of each voice's raw period, and the span accent
    below is then forced to be exactly long enough to inflect the restatements it costs.
    """
    parity = math.lcm(*(note_layers[n] * units[n] for n in note_layers))
    print("\nParity — the first convergence of the raw rhythms:")
    for n in note_layers:
        raw = note_layers[n] * units[n]
        print(f"  {n}: {note_layers[n]} steps x {units[n]} = {raw} ticks, "
              f"restated {parity // raw}x to reach parity")
    print(f"  P = LCM = {parity} ticks = {parity / (TICKS_PER_QUARTER_NOTE * 4):g} bars\n")
    return parity


def accent_field(cfg, base_binaries, note_layers, units, parity,
                 residue_source=None, levels=None, note_at=None):
    """One voice's accents, and — once `levels` is known — its velocities.

    The render and the residue search both come through here, so there is no second
    implementation to drift. `residue_source` overrides config's only while searching.
    `levels` is the piece's shared velocity table; without it the accents are built but
    no velocity is assigned, which is how the table is gathered in the first place.
    """
    name = cfg['name']
    label, expression = span_accent(note_layers[name], parity // units[name], residue_source)
    accent_dict = dict(WEATHER, **{label: expression})
    span = voice_span(note_layers[name], accent_dict)
    binary_full = voice_rhythm(cfg, base_binaries, span)
    # The field is sampled at the voice's OWN step index, always. Rolling it for a canon
    # voice put C under different weather from A and B — see CONTEXT.md on dois_18.
    accent_bins = create_accent_binaries(accent_dict, span)
    field = {'label': label, 'expression': expression, 'accent_dict': accent_dict,
             'span': span, 'accents': accent_bins}
    if levels is not None:
        profile = velocity_profile(accent_bins, levels)
        field['profile'] = profile
        field['notes_per_step'], field['velocities'] = accent_voicing(
            binary_full, accent_bins, profile, note_at or (lambda step: cfg['pitch']))
    return field


def build_voices(field, note_layers, levels, notes_for):
    """Each voice's sounding steps and velocities, with its accents printed."""
    voices = []
    for cfg in INSTRUMENT_CONFIGS:
        name = cfg['name']
        got = field(cfg, levels=levels, note_at=notes_for(cfg, note_layers))
        used = sorted(set(levels.values()))
        gaps = {b - a for a, b in zip(used, used[1:])}
        spacing = str(gaps.pop()) if len(gaps) == 1 else f"{min(gaps)}-{max(gaps)}"
        print(f"  {name}: rhythm {note_layers[name]} steps, accents span {got['span']} "
              f"({got['span'] // note_layers[name]} passes) — {len(used)} shared levels "
              f"{used[0]}-{used[-1]} spaced {spacing}")
        voices.append((name, got['notes_per_step'], got['velocities'], get_step_ticks(cfg)))
    return voices


def require_distinct_passes(voices, note_layers, field):
    """Principle IV, checked BEFORE any file is replaced.

    check.py tests this again from the written files. This is the early warning, and
    for a NEW SIEVE it is the one that matters: the span modulus changes with the
    sieve, and residues that inflected one layer's passes need not inflect another's.
    """
    bare = {name: duplicate_passes(vel, note_layers[name]) for name, _, vel, _ in voices}
    bare = {name: pairs for name, pairs in bare.items() if pairs}
    if not bare:
        return
    found = search_residue_source(field, note_layers)
    advice = (f"SPAN_RESIDUE_SOURCE = {found} inflects every pass of this sieve" if found
              else "no residue set of up to five members worked; the span accent cannot "
                   "inflect every pass at these basic units, so the sieve, the units or "
                   "the weather has to change")
    raise ValueError(
        f"SPAN_RESIDUE_SOURCE = {tuple(SPAN_RESIDUE_SOURCE)} leaves identical passes "
        f"({bare}), so the repetition parity forces would be bare — Principle IV. "
        f"Nothing was written. {advice}.")


def report_span_suggestion(voices, note_layers, field):
    """`--suggest-span`: what to put in config for this sieve. Writes nothing."""
    found = search_residue_source(field, note_layers)
    current = {name: duplicate_passes(vel, note_layers[name]) for name, _, vel, _ in voices}
    print("\n  --suggest-span")
    print(f"    configured SPAN_RESIDUE_SOURCE = {tuple(SPAN_RESIDUE_SOURCE)}: "
          + ("inflects every pass of every voice" if not any(current.values())
             else f"leaves identical passes {({k: v for k, v in current.items() if v})}"))
    print(f"    a set that works for this sieve: {found}" if found else
          "    no residue set of up to five members works for this sieve; the span "
          "accent cannot inflect every pass at these basic units")


def choose_meters(voices, periods, note_layers, total_ticks):
    """One meter for everyone if a bar length fits every period; otherwise per voice."""
    candidate_bars = [note_layers[name] * st for name, _, _, st in voices]
    one = shared_meter(list(periods.values()) + [total_ticks], candidate_bars)
    if one:
        bar = one[0] * (4 * TICKS_PER_QUARTER_NOTE) // one[1]
        print(f"\n  Shared meter {one[0]}/{one[1]} (bar {bar} ticks) — "
              + ", ".join(f"{n} {p // bar} bars" for n, p in periods.items()))
        meters = {name: one for name in periods}
    else:
        print("\n  No single meter fits every period; using per-voice meters.")
        meters = {}
        for name, _, _, step_ticks in voices:
            m = meter_for_voice(step_ticks, note_layers[name] * step_ticks, periods[name])
            if m is None:
                m = TIME_SIGNATURE
                print(f"  !! {name}: no meter lands on {periods[name]} ticks — "
                      f"falling back to {m[0]}/{m[1]}; a host will pad this clip.")
            meters[name] = m
    ensemble_meter = one or meter_for(min(candidate_bars)) or TIME_SIGNATURE
    return meters, ensemble_meter


def write_files(voices, periods, total_ticks, meters, ensemble_meter, parity, prefix):
    """The six files: one per voice, the arrangement, and the merged ensemble."""
    fingerprint = config_fingerprint()
    # No render date in the stamp. It made every re-render rewrite all twelve files
    # with no musical change, which buries a real change in the noise. The fingerprint
    # identifies the configuration AND the code exactly, and git records when.
    stamp = (f"{prefix} cfg={fingerprint} "
             f"parity={parity} tempo={TEMPO_BPM} "
             f"weather={'+'.join(WEATHER)} sieve={INSTRUMENT_CONFIGS[0]['sieve']}")
    print(f"\n  provenance stamped on every track: cfg={fingerprint}")

    names = [f"{prefix}_{n}_prime" for n in periods] + [f"{prefix}_arrangement",
                                                        f"{prefix}_ensemble"]
    clear_our_outputs(names)

    print()
    accents_of = {c['name']: c['accent_dict'] for c in INSTRUMENT_CONFIGS}
    arrangement, merged = [], []
    for channel, (name, notes_per_step, velocities, step_ticks) in enumerate(voices):
        line = f"{stamp} voice={name} accents={'+'.join(accents_of[name])}"
        events = voice_events(notes_per_step, velocities, step_ticks, periods[name])
        save_tracks([make_track(name, events, periods[name], meters[name], line)],
                    f"{prefix}_{name}_prime", periods[name], meters[name])
        full = voice_events(notes_per_step, velocities, step_ticks, total_ticks)
        arrangement.append(make_track(name, full, total_ticks, meters[name], line))
        merged.extend(voice_events(notes_per_step, velocities, step_ticks, total_ticks,
                                   channel=channel))

    print()
    reps = ", ".join(f"{n} x{total_ticks // p}" for n, p in periods.items())
    save_tracks(arrangement, f"{prefix}_arrangement", total_ticks, ensemble_meter,
                note=f", {len(arrangement)} tracks — {reps}")
    save_tracks([make_track(f"{prefix} ensemble", merged, total_ticks, ensemble_meter,
                            f"{stamp} all voices")],
                f"{prefix}_ensemble", total_ticks, ensemble_meter,
                note=", all voices on one track, one MIDI channel each")


def main():
    """The whole process, in order. Every pitch mode is rendered from one rhythm."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    base_binaries, note_layers = derive_note_layers()
    units = {cfg['name']: get_step_ticks(cfg) for cfg in INSTRUMENT_CONFIGS}
    parity = parity_point(note_layers, units)

    def field(cfg, residue_source=None, levels=None, note_at=None):
        return accent_field(cfg, base_binaries, note_layers, units, parity,
                            residue_source, levels, note_at)

    for cfg in INSTRUMENT_CONFIGS:
        got = field(cfg)
        cfg['accent_dict'] = got['accent_dict']
        print(f"  {cfg['name']}: span accent derived — "
              f"modulus {true_period(got['expression'])}, {got['expression']}")

    # ONE velocity table for the whole piece: the same combination of accents means the
    # same velocity in every voice, and in every pitch mode — velocity does not depend
    # on pitch at all, which is why the modes share a rhythm and a dynamic shape.
    levels = shared_velocity_levels({c['name']: field(c)['accents']
                                     for c in INSTRUMENT_CONFIGS})
    print("  velocity table, shared by every voice: "
          + " ".join(str(v) for _, v in sorted(levels.items())))

    print()
    rhythm = build_voices(field, note_layers, levels, lambda cfg, _: (lambda step: 0))
    if '--suggest-span' in sys.argv:
        report_span_suggestion(rhythm, note_layers, field)
        return
    require_distinct_passes(rhythm, note_layers, field)

    periods = {name: len(vel) * st for name, _, vel, st in rhythm}
    total_ticks = math.lcm(*periods.values())
    print("\n  Voice periods (one full statement at that voice's basic unit):")
    for name, _, velocities, step_ticks in rhythm:
        print(f"    {name}: {len(velocities)} steps x {step_ticks} ticks = {periods[name]}")
    print(f"  Ensemble {total_ticks} ticks — "
          + ", ".join(f"{n} x{total_ticks // p}" for n, p in periods.items()))
    meters, ensemble_meter = choose_meters(rhythm, periods, note_layers, total_ticks)

    failed = []
    for mode in PITCH_MODES:
        notes_for, check_mode = MODES[mode]
        print(f"\n{'=' * 70}\nPitch mode {mode!r}: {check_mode(note_layers)}")
        voices = build_voices(field, note_layers, levels, notes_for)
        write_files(voices, periods, total_ticks, meters, ensemble_meter, parity,
                    f"{TITLE}_{mode}")
        if not verify(voices, periods, total_ticks, note_layers, base_binaries,
                      f"{TITLE}_{mode}", mode):
            failed.append(mode)

    if failed:
        print(f"\n  {', '.join(failed)} FAILED verification")
        sys.exit(1)


if __name__ == '__main__':
    main()
