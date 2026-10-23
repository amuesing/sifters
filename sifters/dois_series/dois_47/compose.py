"""Run the composition: config -> voices -> files -> checks.

    python3 compose.py                    the piece in config.py: the MIDI into mid/, the
                                          wavetables into wavetables/, the Serum presets
                                          into presets/
        --install-serum                   also install the wavetables and presets in Serum
        --suggest-span                    report on the span residues, write nothing
"""
import sys

if sys.version_info < (3, 14):
    sys.exit(f"sifters needs Python 3.14 or later (the Serum presets are compressed with its "
             f"compression.zstd); this is Python {sys.version.split()[0]}")

import hashlib
import importlib.metadata
import json
import math
import os
from dataclasses import dataclass

import numpy as np

import config
from sieve import evaluate, build_binary, true_period, voice_rhythm
from accents import (derive_weather, create_accent_binaries, duplicate_passes, notes_for_steps,
                     shared_velocity_levels, span_accent, states_reachable, velocities_of,
                     voice_span)
from span import (derive_span_residues, describe_apart, format_residues, states_used,
                  try_residues, weakest_pass_difference)
from midi import (commit_staged, output_dir, get_step_ticks, make_track, meter_for, staged_output,
                  meter_for_voice, save_tracks, shared_meter, voice_events)
from check import check_presets, check_wavetables, verify
from wavetable import (install_into_serum, serum_folder, serum_presets_folder,
                       serum_tables_folder, write_wavetables)
from serum import install_presets, presets_folder, write_presets

HERE = os.path.dirname(os.path.abspath(__file__))
OPTIONS = ('--install-serum', '--suggest-span')


@dataclass
class Voice:
    """One voice's notes, velocities, timing and accents."""
    name: str
    notes: list[list[int]]
    velocities: np.ndarray
    step_ticks: int
    accents: dict[str, str]


# ------------------------------------------------------------------- provenance

def config_fingerprint():
    """A short hash of everything that determines the output: settings, code, libraries.
    Not where the project sits: the output folders and config's own `_HERE` are left out,
    so the same piece renders the same bytes in any folder."""
    settings = {key: value for key, value in sorted(vars(config).items())
                if key.isupper() and not key.startswith('_') and key != 'OUTPUT_DIRS'}
    source = {name: hashlib.sha256(open(os.path.join(HERE, name), 'rb').read()).hexdigest()
              for name in sorted(os.listdir(HERE)) if name.endswith('.py')}
    libraries = {name: importlib.metadata.version(name)
                 for name in ('mido', 'music21', 'numpy')}
    document = json.dumps({'settings': settings, 'source': source,
                           'libraries': libraries}, sort_keys=True, default=repr)
    return hashlib.sha256(document.encode()).hexdigest()[:8]


def provenance(prefix, parity, weather):
    """The text stamped on every track: what made it, never when (so a re-render with
    no musical change rewrites nothing)."""
    return (f"{prefix} cfg={config_fingerprint()} "
            f"parity={parity} tempo={config.TEMPO_BPM} "
            f"weather={'+'.join(weather)} sieve={config.INSTRUMENT_CONFIGS[0]['sieve']}")


# ------------------------------------------------------- the rhythm and its parity

def derive_note_layers():
    """Every voice's pattern and the period it actually closes on: measured, never
    declared, so an independent sieve or an early-closing derivation carries its own."""
    base_binaries, note_layers = {}, {}
    for cfg in config.INSTRUMENT_CONFIGS:
        binary, period = build_binary(cfg, base_binaries)
        base_binaries[cfg['name']] = binary
        note_layers[cfg['name']] = period

    distinct = sorted(set(note_layers.values()))
    print("Note layers (each derived from that voice's own sieve): "
          + ", ".join(f"{n} {p}" for n, p in note_layers.items())
          + (f"  — all {distinct[0]} steps\n" if len(distinct) == 1
             else f"  — {len(distinct)} different periods in play\n"))
    print("Densities:")
    for cfg in config.INSTRUMENT_CONFIGS:
        b = base_binaries[cfg['name']]
        print(f"  {cfg['name']}: {b.sum()}/{len(b)} steps ({100 * b.mean():.1f}%)")
    return base_binaries, note_layers


def parity_point(note_layers, units):
    """P: the first tick at which every voice has finished a whole number of layers."""
    parity = math.lcm(*(note_layers[n] * units[n] for n in note_layers))
    print("\nParity — the first convergence of the raw rhythms:")
    for n in note_layers:
        raw = note_layers[n] * units[n]
        print(f"  {n}: {note_layers[n]} steps x {units[n]} = {raw} ticks, "
              f"restated {parity // raw}x to reach parity")
    print(f"  P = LCM = {parity} ticks = {parity / (config.TICKS_PER_QUARTER_NOTE * 4):g} bars\n")
    return parity


def pass_capacity(base_binaries, note_layers, units, parity):
    """How many DIFFERENT passes each voice could possibly have: (attacks, passes, 2**k).

    The weather marks every pass the same way and only the span accent varies, so k
    attacks allow at most 2**k distinguishable passes. Necessary, not sufficient: only
    the failure direction proves anything.
    """
    capacity = {}
    for name, layer in note_layers.items():
        attacks = int(base_binaries[name].sum())
        passes = parity // (layer * units[name])
        capacity[name] = (attacks, passes, 2 ** attacks)
    return capacity


def require_pass_capacity(capacity, note_layers, units, parity):
    """Refuse a sieve whose voices cannot have distinct passes, with the count as proof."""
    over = {n: v for n, v in capacity.items() if v[1] > v[2]}
    if not over:
        return
    lines = []
    for name, (attacks, passes, most) in over.items():
        lines.append(
            f"    {name}: {attacks} attack(s) in a {note_layers[name]}-step layer, "
            f"restated {passes}x to reach parity, but at most 2**{attacks} = {most} "
            f"different passes are possible — {passes} > {most}")
    raise ValueError(
        "these voices cannot have distinct passes at these basic units, and no residue "
        "set can change that — Principle IV:\n" + "\n".join(lines) + "\n"
        f"  First parity itself is fine: it exists, at {parity} ticks. What cannot be "
        "done is telling the restatements apart. The weather is static, so it marks the "
        "same attacks identically on every pass; only the span accent varies, and one "
        "binary accent over k attacks gives 2**k patterns. This is a COUNT, not a failed "
        "search. Change the basic units, the sieve, or the accent design. "
        "Nothing was written.")


def state_ceilings(base_binaries, weather, note_layers, passes=None):
    """The most velocity states each voice could possibly use: per weather combination
    its attacks meet, one or two depending on how often it occurs (states_reachable)."""
    firing = {label: evaluate(expr, max(note_layers.values()))
              for label, expr in weather.items()}
    passes = passes or {}
    return {name: states_reachable(binary, firing, list(weather), passes.get(name, 2))
            for name, binary in base_binaries.items()}


def require_static_weather(weather, note_layers):
    """The weather's TRUE period must divide every note layer, or it would move against
    the layer and push the piece past first parity."""
    for label, expression in weather.items():
        period = true_period(expression, quiet=True)
        against = {name: layer for name, layer in note_layers.items() if layer % period}
        if against:
            raise ValueError(
                f"weather {label!r} = {expression!r} has period {period}, which does not "
                f"divide these note layers: {against}. A weather accent must be static "
                f"within the layer — one that moves is a span accent, and it would push "
                f"the piece past first parity. Nothing was written.")


# ------------------------------------------------------------------ the accents

def accent_field(cfg, base_binaries, note_layers, units, parity, weather,
                 residue_source, quiet=False):
    """One voice's accents and its full rhythm. The render and the residue search both
    come through here, so there is no second implementation to drift."""
    name = cfg['name']
    label, expression = span_accent(note_layers[name], parity // units[name],
                                    residue_source, quiet)
    accent_dict = dict(weather, **{label: expression})
    span = voice_span(note_layers[name], accent_dict)
    # Sampled at the voice's OWN step index, so every voice is under one weather.
    return {'label': label, 'expression': expression, 'accent_dict': accent_dict,
            'span': span, 'accents': create_accent_binaries(accent_dict, span),
            'rhythm': voice_rhythm(cfg, base_binaries, span)}


def span_residues(field, note_layers, ceilings, units, parity, base_binaries):
    """The span residues: config's, reported against the search's own measures, or
    derived by the search."""
    if config.SPAN_RESIDUES:
        source = {int(m): tuple(r) for m, r in config.SPAN_RESIDUES.items()}
        got = try_residues(field, note_layers, source)
        if got is None:
            print(f"  span residues (from config): {format_residues(source)}")
        else:
            got_fields, got_levels = got
            used = states_used(got_fields, got_levels)
            apart = weakest_pass_difference(got_fields, got_levels, note_layers)
            at_ceiling = all(used[n] >= ceilings[n] for n in used)
            print(f"  span residues (from config): {format_residues(source)} — "
                  + ("every voice at its ceiling (" if at_ceiling else "states used (")
                  + ", ".join(f"{n} {used[n]}/{ceilings[n]}" for n in used)
                  + "); " + describe_apart(apart))
        return source
    source, used, apart, how = derive_span_residues(field, note_layers, ceilings,
                                                    units, parity, base_binaries)
    for modulus in sorted(how, reverse=True):
        print(f"  span modulus {modulus}: {how[modulus]}")
    print(f"  span residues (derived): {format_residues(source)} — every voice at its "
          f"ceiling (" + ", ".join(f"{n} {used[n]}/{ceilings[n]}" for n in used)
          + "); " + describe_apart(apart))
    return source


def prepare_accents(field, note_layers, source):
    """Every voice's accents, the piece's one velocity table, and the velocities, all
    computed ONCE."""
    fields = {cfg['name']: field(cfg, source) for cfg in config.INSTRUMENT_CONFIGS}
    for cfg in config.INSTRUMENT_CONFIGS:
        got = fields[cfg['name']]
        print(f"  {cfg['name']}: span accent derived — "
              f"modulus {true_period(got['expression'])}, {got['expression']}")

    levels = shared_velocity_levels({n: f['accents'] for n, f in fields.items()})
    print("  velocity table, shared by every voice: "
          + " ".join(str(v) for _, v in sorted(levels.items())))
    for got in fields.values():
        got['velocities'] = velocities_of(got, levels)

    print()
    used = sorted(set(levels.values()))
    gaps = {b - a for a, b in zip(used, used[1:])}
    spacing = str(gaps.pop()) if len(gaps) == 1 else f"{min(gaps)}-{max(gaps)}"
    for name, got in fields.items():
        print(f"  {name}: rhythm {note_layers[name]} steps, accents span {got['span']} "
              f"({got['span'] // note_layers[name]} passes) — {len(used)} shared levels "
              f"{used[0]}-{used[-1]} spaced {spacing}")
    return fields


def identical_passes(fields, note_layers):
    found = {name: duplicate_passes(f['velocities'], note_layers[name])
             for name, f in fields.items()}
    return {name: pairs for name, pairs in found.items() if pairs}


def report_span_suggestion(fields, note_layers, source, derived):
    """`--suggest-span`: whether the residues in use make every pass distinct."""
    bare = identical_passes(fields, note_layers)
    print("\n  --suggest-span")
    print(f"    span residues in use {format_residues(source)} "
          + ("(derived)" if derived else "(from config)") + ": "
          + ("every pass distinct" if not bare else f"leaves identical passes {bare}"))


def require_distinct_passes(fields, note_layers, source):
    """Principle IV, checked BEFORE any file is replaced (check.py checks it again)."""
    bare = identical_passes(fields, note_layers)
    if bare:
        raise ValueError(
            f"SPAN_RESIDUES = {format_residues(source)} leaves identical passes ({bare}), so "
            f"the repetition parity forces would be bare — Principle IV. Nothing was written. "
            f"Run `python3 compose.py --suggest-span` to see how this set does against the "
            f"sieve, or set SPAN_RESIDUES = None and let the search choose.")


def require_first_parity(periods, parity):
    """Parity must be the FIRST convergence (Principle II), checked before writing."""
    if set(periods.values()) != {parity}:
        raise ValueError(
            f"voice periods {periods} are not all the first convergence {parity}. The "
            f"accents must span exactly the restatements parity requires, no more and "
            f"no fewer — Principle II. Nothing was written.")


# ------------------------------------------------------------------- writing

def choose_meters(note_layers, periods, units, total_ticks):
    """One meter for everyone if a bar length fits every period; otherwise per voice."""
    candidate_bars = [note_layers[name] * units[name] for name in periods]
    one = shared_meter(list(periods.values()) + [total_ticks], candidate_bars)
    if one:
        bar = one[0] * (4 * config.TICKS_PER_QUARTER_NOTE) // one[1]
        print(f"\n  Shared meter {one[0]}/{one[1]} (bar {bar} ticks) — "
              + ", ".join(f"{n} {p // bar} bars" for n, p in periods.items()))
        meters = {name: one for name in periods}
    else:
        print("\n  No single meter fits every period; using per-voice meters.")
        meters = {}
        for name in periods:
            step_ticks = units[name]
            m = meter_for_voice(step_ticks, note_layers[name] * step_ticks, periods[name])
            if m is None:
                m = config.TIME_SIGNATURE
                print(f"  !! {name}: no meter lands on {periods[name]} ticks — "
                      f"falling back to {m[0]}/{m[1]}; a host will pad this clip.")
            meters[name] = m
    ensemble_meter = one or meter_for(min(candidate_bars)) or config.TIME_SIGNATURE
    return meters, ensemble_meter


def check_pitches():
    """Whole-number MIDI notes, one per voice, all different: checked before writing."""
    for cfg in config.INSTRUMENT_CONFIGS:
        value = cfg['pitch']
        if type(value) is not int or not 0 <= value <= 127:
            raise ValueError(f"voice {cfg['name']}: pitch must be a whole number in "
                             f"0..127, got {value!r}. Nothing was written.")
    if len({c['pitch'] for c in config.INSTRUMENT_CONFIGS}) != len(config.INSTRUMENT_CONFIGS):
        raise ValueError("two voices share a pitch; a Drum Rack could not tell them apart. "
                         "Nothing was written.")
    return ", ".join(f"{c['name']}={c['pitch']}" for c in config.INSTRUMENT_CONFIGS)


def build_voices(fields):
    """Each voice: its one note wherever it sounds."""
    return [Voice(name=cfg['name'],
                  notes=notes_for_steps(fields[cfg['name']]['velocities'],
                                        lambda step, note=cfg['pitch']: note),
                  velocities=fields[cfg['name']]['velocities'],
                  step_ticks=get_step_ticks(cfg),
                  accents=fields[cfg['name']]['accent_dict'])
            for cfg in config.INSTRUMENT_CONFIGS]


def write_set(voices, total_ticks, meters, ensemble_meter, parity, prefix, weather):
    """`<prefix>.mid`: one track per voice, named for it, each its whole statement.
    Dragged into a DAW it becomes one track per voice."""
    stamp = provenance(prefix, parity, weather)
    print(f"\n  provenance stamped on every track: cfg={config_fingerprint()}\n")
    tracks = []
    for voice in voices:
        line = f"{stamp} voice={voice.name} accents={'+'.join(voice.accents)}"
        events = voice_events(voice.notes, voice.velocities, voice.step_ticks, total_ticks)
        tracks.append(make_track(voice.name, events, total_ticks, meters[voice.name], line))
    save_tracks(tracks, prefix, total_ticks, ensemble_meter,
                note=f", a track per voice: {', '.join(v.name for v in voices)}")
    return [prefix]


def render_midi(fields, note_layers, base_binaries, periods, total_ticks, meters,
                ensemble_meter, parity, weather, pitches, written, failed):
    """The MIDI file, written and verified."""
    print(f"\n{'=' * 70}\nThe MIDI: a track per voice, each on one note ({pitches})")
    voices = build_voices(fields)
    written += write_set(voices, total_ticks, meters, ensemble_meter, parity, config.TITLE,
                         weather)
    if not verify(voices, periods, total_ticks, note_layers, base_binaries, config.TITLE,
                  weather, parity):
        failed.append('MIDI')


def render_wavetables(base_binaries, written, failed):
    print(f"\n{'=' * 70}\nSerum wavetables: a frame for every whole number a note "
          f"or velocity can be, each one period of the sieve in its own register\n")
    written += write_wavetables(base_binaries, config.TITLE, output_dir('wavetables'))
    problems = check_wavetables(base_binaries, config.TITLE)
    for problem in problems:
        print(f"    - {problem}")
    if problems:
        failed.append('wavetables')
    else:
        print("  wavetables verified: Serum 2's format and a non-factory marker; "
              "every frame's harmonics measured with an FFT and matched to the sieve "
              "(read from the frame's number, sounded from its cut, equal strength, "
              "in phase); one level across every frame")


def render_presets(base_binaries, units, written, failed):
    print(f"\n{'=' * 70}\nSerum presets: one per voice, named for its track, the voice's "
          f"drum frequency-modulated by its complement\n")
    written += write_presets(base_binaries, units, output_dir('presets'))
    problems = check_presets(base_binaries, units, config.TITLE)
    for problem in problems:
        print(f"    - {problem}")
    if problems:
        failed.append('presets')
    else:
        print("  presets verified: each read back by a reader of its own (container, hash, "
              "CBOR), and every derived number recomputed: pitch from OCT/SEM/FINE, decays, "
              "strike, the 1:1, tables and routings")


# ------------------------------------------------------------------------ the run

def next_steps():
    """What to open, printed after a render: the set file and the preset for each track."""
    mid = os.path.relpath(os.path.join(config.OUTPUT_DIRS['mid'], f"{config.TITLE}.mid"), HERE)
    names = [cfg['name'] for cfg in config.INSTRUMENT_CONFIGS]
    folder = serum_folder()
    print(f"\n  Next, in Ableton, at {config.TEMPO_BPM} BPM:"
          f"\n    1. drag {mid} in: one track per voice, {', '.join(names)}"
          f"\n    2. on each track, Serum with the preset of the same name ('{folder} "
          f"{names[0]}' ...), under User > {config.SERUM_PROJECT} > {folder}")
    if '--install-serum' not in sys.argv:
        print("    (run once with --install-serum to put the presets and tables in Serum)")


def main():
    """The whole process, in order."""
    unknown = [arg for arg in sys.argv[1:] if arg.startswith('-') and arg not in OPTIONS]
    if unknown:
        sys.exit(f"unknown option(s) {unknown}; compose.py takes {', '.join(OPTIONS)} "
                 f"(see the top of compose.py). Nothing was written.")

    base_binaries, note_layers = derive_note_layers()
    units = {cfg['name']: get_step_ticks(cfg) for cfg in config.INSTRUMENT_CONFIGS}
    parity = parity_point(note_layers, units)
    # How often each voice states its rhythm before parity.
    passes = {n: parity // (note_layers[n] * units[n]) for n in note_layers}

    weather = config.WEATHER or derive_weather(base_binaries,
                                               config.INSTRUMENT_CONFIGS[0]['sieve'],
                                               note_layers, passes=passes)
    print("\nWeather " + ("(from config)" if config.WEATHER else "(derived from the sieve)")
          + ": " + ", ".join(f"{k} = {v}" for k, v in weather.items()))
    require_static_weather(weather, note_layers)
    require_pass_capacity(pass_capacity(base_binaries, note_layers, units, parity),
                          note_layers, units, parity)

    def field(cfg, residue_source, quiet=False):
        return accent_field(cfg, base_binaries, note_layers, units, parity, weather,
                            residue_source, quiet)

    ceilings = state_ceilings(base_binaries, weather, note_layers, passes)
    source = span_residues(field, note_layers, ceilings, units, parity, base_binaries)
    fields = prepare_accents(field, note_layers, source)
    if '--suggest-span' in sys.argv:
        report_span_suggestion(fields, note_layers, source, not config.SPAN_RESIDUES)
        return
    require_distinct_passes(fields, note_layers, source)

    periods = {name: len(f['velocities']) * units[name] for name, f in fields.items()}
    require_first_parity(periods, parity)
    total_ticks = math.lcm(*periods.values())
    print("\n  Voice periods (one full statement at that voice's basic unit):")
    for name, f in fields.items():
        print(f"    {name}: {len(f['velocities'])} steps x {units[name]} ticks "
              f"= {periods[name]}")
    print(f"  Ensemble {total_ticks} ticks — "
          + ", ".join(f"{n} x{total_ticks // p}" for n, p in periods.items()))
    meters, ensemble_meter = choose_meters(note_layers, periods, units, total_ticks)

    # The pitches are checked before ANY writes, and everything renders into a staging
    # folder: nothing moves into place until every file has been written and verified.
    pitches = check_pitches()
    failed, written = [], []
    with staged_output():
        render_midi(fields, note_layers, base_binaries, periods, total_ticks, meters,
                    ensemble_meter, parity, weather, pitches, written, failed)
        if config.WAVETABLES and not failed:
            render_wavetables(base_binaries, written, failed)
        if config.SERUM_PRESETS and config.WAVETABLES and not failed:
            render_presets(base_binaries, units, written, failed)
        if failed:
            print(f"\n  {', '.join(failed)} FAILED verification — nothing was moved, "
                  f"the files you had are still there")
            sys.exit(1)
        commit_staged(written)

    # Only on request: the one thing that writes outside the project.
    if '--install-serum' in sys.argv and config.WAVETABLES:
        folder = serum_tables_folder()
        copied = install_into_serum(config.OUTPUT_DIRS['wavetables'], written, folder)
        print(f"\n  {len(copied)} wavetable(s) installed in Serum: {folder}"
              f"\n  In Serum, pick them from an oscillator's wavetable menu, under "
              f"'{os.path.basename(folder)}'.")
        if config.SERUM_PRESETS:
            target = presets_folder(serum_presets_folder())
            copied = install_presets(config.OUTPUT_DIRS['presets'], written, target)
            print(f"  {len(copied)} preset(s) installed in Serum's browser: {target}")
    if config.SERUM_PRESETS and config.WAVETABLES:
        next_steps()


if __name__ == '__main__':
    main()
