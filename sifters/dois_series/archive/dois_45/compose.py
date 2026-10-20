"""Run the composition: config -> voices -> MIDI files -> checks.

    python3 compose.py                    the piece in config.py: MIDI into mid/,
                                          wavetables into wavetables/, tuning into tuning/
        --piece eight_five                a piece from pieces/ instead, into an
                                          eight_five/ folder inside each
        --suggest-span                    report on the span residues, write nothing
        --install-serum                   also copy the wavetables into Serum
"""
import hashlib
import importlib.metadata
import importlib.util
import json
import math
import os
import sys
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
from check import check_form, check_tuning, check_wavetables, verify
from form import write_form
from tuning import tuning_period, write_tuning
from wavetable import install_into_serum, serum_tables_folder, write_wavetables
from pitch import MODES

HERE = os.path.dirname(os.path.abspath(__file__))


@dataclass
class Voice:
    """One pitch mode's notes, with the shared velocities, timing and accents."""
    name: str
    notes: list[list[int]]
    velocities: np.ndarray
    step_ticks: int
    accents: dict[str, str]


# ------------------------------------------------------------------------ pieces

def load_piece(name):
    """Lay pieces/<name>.py over config.py: a piece names only what it changes, and
    VOICES changes the named voices' settings. Its files go to a <name>/ folder inside
    each output folder."""
    path = os.path.join(HERE, 'pieces', f'{name}.py')
    if not os.path.exists(path):
        known = sorted(p[:-3] for p in os.listdir(os.path.join(HERE, 'pieces'))
                       if p.endswith('.py'))
        sys.exit(f"no piece {name!r}; pieces/ has {known}")
    spec = importlib.util.spec_from_file_location(f'pieces.{name}', path)
    piece = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(piece)
    for key, value in vars(piece).items():
        if key == 'VOICES':
            for cfg in config.INSTRUMENT_CONFIGS:
                cfg.update(value.get(cfg['name'], {}))
        elif key.isupper():
            setattr(config, key, value)
    config.OUTPUT_DIRS = {kind: os.path.join(folder, name)
                          for kind, folder in config.OUTPUT_DIRS.items()}
    print(f"Piece {name!r}: pieces/{name}.py over config.py\n")


# ------------------------------------------------------------------- provenance

def config_fingerprint():
    """A short hash of everything that determines the output: settings, code, libraries."""
    settings = {key: value for key, value in sorted(vars(config).items())
                if key.isupper() and key != 'OUTPUT_DIRS'}
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
    computed ONCE: velocity never depends on pitch, so the pitch modes share it."""
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


def build_voices(fields, notes_for, note_layers):
    """Each voice for one pitch mode. Only the notes differ between modes."""
    return [Voice(name=cfg['name'],
                  notes=notes_for_steps(fields[cfg['name']]['velocities'],
                                        notes_for(cfg, note_layers)),
                  velocities=fields[cfg['name']]['velocities'],
                  step_ticks=get_step_ticks(cfg),
                  accents=fields[cfg['name']]['accent_dict'])
            for cfg in config.INSTRUMENT_CONFIGS]


def write_files(voices, periods, total_ticks, meters, ensemble_meter, parity, prefix,
                weather):
    """The six files: one per voice, the arrangement, and the merged ensemble."""
    stamp = provenance(prefix, parity, weather)
    print(f"\n  provenance stamped on every track: cfg={config_fingerprint()}")

    print()
    arrangement, merged = [], []
    for channel, voice in enumerate(voices):
        name = voice.name
        line = f"{stamp} voice={name} accents={'+'.join(voice.accents)}"
        events = voice_events(voice.notes, voice.velocities, voice.step_ticks, periods[name])
        save_tracks([make_track(name, events, periods[name], meters[name], line)],
                    f"{prefix}_{name}_prime", periods[name], meters[name])
        full = voice_events(voice.notes, voice.velocities, voice.step_ticks, total_ticks)
        arrangement.append(make_track(name, full, total_ticks, meters[name], line))
        merged.extend(voice_events(voice.notes, voice.velocities, voice.step_ticks,
                                   total_ticks, channel=channel))

    print()
    reps = ", ".join(f"{n} x{total_ticks // p}" for n, p in periods.items())
    save_tracks(arrangement, f"{prefix}_arrangement", total_ticks, ensemble_meter,
                note=f", {len(arrangement)} tracks — {reps}")
    save_tracks([make_track(f"{prefix} ensemble", merged, total_ticks, ensemble_meter,
                            f"{stamp} all voices")],
                f"{prefix}_ensemble", total_ticks, ensemble_meter,
                note=", all voices on one track, one MIDI channel each")
    return [f"{prefix}_{n}_prime" for n in periods] + [f"{prefix}_arrangement",
                                                       f"{prefix}_ensemble"]


def render_modes(fields, note_layers, base_binaries, periods, total_ticks, meters,
                 ensemble_meter, parity, weather, described, written, failed):
    """Every pitch mode, written and verified; the forms where pitch can move. Returns
    one mode's voices, for the wavetable check."""
    voices = None
    for mode in config.PITCH_MODES:
        notes_for, _ = MODES[mode]
        print(f"\n{'=' * 70}\nPitch mode {mode!r}: {described[mode]}")
        voices = build_voices(fields, notes_for, note_layers)
        prefix = f"{config.TITLE}_{mode}"
        written += write_files(voices, periods, total_ticks, meters, ensemble_meter,
                               parity, prefix, weather)
        # Static sections with the same voices would repeat, so static has no form.
        has_form = config.FORM and mode != 'static'
        if has_form:
            written.append(write_form(voices, notes_for, note_layers, base_binaries,
                                      parity, ensemble_meter, prefix,
                                      provenance(prefix, parity, weather)))
        if not verify(voices, periods, total_ticks, note_layers, base_binaries,
                      prefix, mode, weather, parity):
            failed.append(mode)
        elif has_form:
            problems = check_form(voices, note_layers, base_binaries, parity, prefix, mode)
            for problem in problems:
                print(f"    - {problem}")
            if problems:
                failed.append(f"{mode} form")
    return voices


def render_wavetables(fields, base_binaries, voices, periods, written, failed):
    print(f"\n{'=' * 70}\nSerum wavetables: a frame for every whole number a note "
          f"or velocity can be, each one period of the sieve in its own register\n")
    written += write_wavetables(fields, base_binaries, config.TITLE, output_dir('wavetables'))
    problems = check_wavetables(voices, periods, base_binaries, config.TITLE)
    for problem in problems:
        print(f"    - {problem}")
    if problems:
        failed.append('wavetables')
    else:
        print("  wavetables verified: Serum 2's format and a non-factory marker; "
              "every frame's harmonics measured with an FFT and matched to the sieve "
              "(read from the frame's number, sounded from its cut, equal strength, "
              "in phase); one level "
              "across every frame; the sweep against the velocities in the written "
              "MIDI; and the .txt sidecars")


def render_tuning(written, failed):
    print(f"\n{'=' * 70}\nTuning: the sieve's period as one octave, for the "
          f"lattice and canon sets\n")
    written += write_tuning(config.TITLE, output_dir('tuning'))
    problems = check_tuning(config.TITLE, tuning_period())
    for problem in problems:
        print(f"    - {problem}")
    if problems:
        failed.append('tuning')
    else:
        print("  tuning verified: .tun (every MIDI note, rounded and exact), .scl "
              "and .kbm, each read back by a parser of its own")


# ------------------------------------------------------------------------ the run

def main():
    """The whole process, in order. Every pitch mode is rendered from one rhythm."""
    if '--piece' in sys.argv:
        at = sys.argv.index('--piece') + 1
        if at == len(sys.argv):
            sys.exit("--piece needs a name from pieces/, e.g. --piece eight_five")
        load_piece(sys.argv[at])

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

    # Every mode is checked before ANY writes, and everything renders into a staging
    # folder: nothing moves into place until every file has been written and verified.
    described = {mode: MODES[mode][1](note_layers) for mode in config.PITCH_MODES}
    failed, written = [], []
    with staged_output():
        voices = render_modes(fields, note_layers, base_binaries, periods, total_ticks,
                              meters, ensemble_meter, parity, weather, described,
                              written, failed)
        if config.WAVETABLES and not failed:
            render_wavetables(fields, base_binaries, voices, periods, written, failed)
        if (config.TUNING and not failed
                and any(mode in ('lattice', 'canon') for mode in config.PITCH_MODES)):
            render_tuning(written, failed)
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


if __name__ == '__main__':
    main()
