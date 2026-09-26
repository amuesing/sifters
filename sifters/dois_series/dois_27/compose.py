"""Run the composition: config -> voices -> MIDI files -> checks."""
import hashlib
import itertools
import importlib.metadata
import json
import math
import os
import sys

import config
from sieve import build_binary, true_period, voice_rhythm
from accents import (derive_weather, create_accent_binaries, duplicate_passes, notes_for_steps,
                     shared_velocity_levels, span_accent, step_velocities,
                     voice_span)
from midi import (clear_our_outputs, get_step_ticks, make_track, meter_for,
                  meter_for_voice, save_tracks, shared_meter, voice_events)
from check import verify
from pitch import MODES
from voice import Voice


def config_fingerprint():
    """A short hash of everything that determines the output."""
    settings = {}
    for key, value in sorted(vars(config).items()):
        if not key.isupper() or key == 'OUTPUT_DIR':
            continue
        settings[key] = value
    here = os.path.dirname(os.path.abspath(__file__))
    source = {name: hashlib.sha256(open(os.path.join(here, name), 'rb').read()).hexdigest()
              for name in sorted(os.listdir(here)) if name.endswith('.py')}
    libraries = {name: importlib.metadata.version(name)
                 for name in ('mido', 'music21', 'numpy')}
    document = json.dumps({'settings': settings, 'source': source,
                           'libraries': libraries}, sort_keys=True, default=repr)
    return hashlib.sha256(document.encode()).hexdigest()[:8]


def try_residues(field, note_layers, candidate):
    """Build every voice with this residue set. Returns (fields, levels) or None."""
    try:
        fields = {c['name']: field(c, candidate) for c in config.INSTRUMENT_CONFIGS}
        levels = shared_velocity_levels({n: f['accents'] for n, f in fields.items()})
    except ValueError:
        return None
    if any(duplicate_passes(velocities_of(f, levels), note_layers[n])
           for n, f in fields.items()):
        return None
    return fields, levels


def derive_span_residues(field, note_layers, accent_count, largest=16, most=5):
    """The span accent's residues, searched rather than written by hand.

    The span accent's one job is to make every restatement parity forces sound
    different. Which residues manage that depends on the sieve — on its period, its
    density and the derived span modulus — so they are found rather than chosen:
    candidate sets are tried in a fixed order, smallest first then lexicographic, and
    the first is kept that

      (a) leaves no two passes of any voice identical, and
      (b) reaches every accent state, so no velocity in the shared table goes unused.

    If nothing reaches every state, the first set satisfying (a) is used and the
    shortfall is reported: a usable piece beats a refusal, but you are told.
    """
    target = 1 << accent_count
    fallback = None
    for size in range(1, most + 1):
        for candidate in itertools.combinations(range(largest), size):
            got = try_residues(field, note_layers, candidate)
            if got is None:
                continue
            fields, levels = got
            reached = len({int(v) for f in fields.values()
                           for v in velocities_of(f, levels) if v})
            if reached == target:
                return candidate, reached, target
            if fallback is None:
                fallback = (candidate, reached, target)
    if fallback is None:
        raise ValueError(
            "no span-accent residues up to five members leave every pass distinct for "
            "this sieve, so the repetition parity forces would be bare — Principle IV. "
            "The sieve, the basic units or the weather has to change.")
    return fallback


def derive_note_layers():
    """Every voice's pattern, and the period each one actually closes on.

    Measured, never declared. They coincide for this composition because all four
    descend from one sieve, but nothing assumes it: an independent sieve of another
    period, or a derivation that closes sooner than its sources, carries its own.
    """
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
    print(f"  P = LCM = {parity} ticks = {parity / (config.TICKS_PER_QUARTER_NOTE * 4):g} bars\n")
    return parity


def accent_field(cfg, base_binaries, note_layers, units, parity, weather, residue_source):
    """One voice's accents and its full rhythm. Nothing here knows about pitch.

    The render and the residue search both come through here, so there is no second
    implementation to drift. `residue_source` overrides config's only while searching.
    """
    name = cfg['name']
    label, expression = span_accent(note_layers[name], parity // units[name], residue_source)
    accent_dict = dict(weather, **{label: expression})
    span = voice_span(note_layers[name], accent_dict)
    # The field is sampled at the voice's OWN step index, always. Rolling it for a canon
    # voice put C under different weather from A and B — see CONTEXT.md on dois_18.
    return {'label': label, 'expression': expression, 'accent_dict': accent_dict,
            'span': span, 'accents': create_accent_binaries(accent_dict, span),
            'rhythm': voice_rhythm(cfg, base_binaries, span)}


def velocities_of(field, levels):
    """A voice's velocities, given the piece's shared table."""
    return step_velocities(field['rhythm'], field['accents'],
                           levels)


def build_voices(fields, notes_for, note_layers):
    """Assemble each voice for one pitch mode. Only the notes differ between modes."""
    voices = []
    for cfg in config.INSTRUMENT_CONFIGS:
        field = fields[cfg['name']]
        voices.append(Voice(
            name=cfg['name'],
            notes=notes_for_steps(field['velocities'], notes_for(cfg, note_layers)),
            velocities=field['velocities'],
            step_ticks=get_step_ticks(cfg),
            accents=field['accent_dict'],
        ))
    return voices



def describe_accents(fields, note_layers, levels):
    """Print each voice's accent span once — it is the same for every pitch mode."""
    used = sorted(set(levels.values()))
    gaps = {b - a for a, b in zip(used, used[1:])}
    spacing = str(gaps.pop()) if len(gaps) == 1 else f"{min(gaps)}-{max(gaps)}"
    for name, field in fields.items():
        print(f"  {name}: rhythm {note_layers[name]} steps, accents span {field['span']} "
              f"({field['span'] // note_layers[name]} passes) — {len(used)} shared levels "
              f"{used[0]}-{used[-1]} spaced {spacing}")


def require_distinct_passes(fields, note_layers, source):
    """Principle IV, checked BEFORE any file is replaced.

    check.py tests this again from the written files. This is the early warning, and
    for a NEW SIEVE it is the one that matters: the span modulus changes with the
    sieve, and residues that inflected one layer's passes need not inflect another's.
    """
    bare = {name: duplicate_passes(f['velocities'], note_layers[name])
            for name, f in fields.items()}
    bare = {name: pairs for name, pairs in bare.items() if pairs}
    if not bare:
        return
    found = search_residue_source(field, note_layers)
    advice = (f"SPAN_RESIDUE_SOURCE = {found} inflects every pass of this sieve" if found
              else "no residue set of up to five members worked; the span accent cannot "
                   "inflect every pass at these basic units, so the sieve, the units or "
                   "the weather has to change")
    raise ValueError(
        f"SPAN_RESIDUE_SOURCE = {tuple(config.SPAN_RESIDUE_SOURCE)} leaves identical passes "
        f"({bare}), so the repetition parity forces would be bare — Principle IV. "
        f"Nothing was written. {advice}.")


def report_span_suggestion(fields, note_layers, source, derived):
    """`--suggest-span`: what the span accent needs for this sieve. Writes nothing.

    With residues derived, this mostly confirms; it earns its keep when config names a
    set explicitly and you want to know whether that set still suits the sieve.
    """
    current = {name: duplicate_passes(f['velocities'], note_layers[name])
               for name, f in fields.items()}
    print("\n  --suggest-span")
    print(f"    span residues in use {source} "
          + ("(derived)" if derived else "(from config)") + ": "
          + ("every pass distinct" if not any(current.values())
             else f"leaves identical passes {({k: v for k, v in current.items() if v})}"))


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


def write_files(voices, periods, total_ticks, meters, ensemble_meter, parity, prefix,
                weather):
    """The six files: one per voice, the arrangement, and the merged ensemble."""
    fingerprint = config_fingerprint()
    # No render date in the stamp. It made every re-render rewrite all twelve files
    # with no musical change, which buries a real change in the noise. The fingerprint
    # identifies the configuration AND the code exactly, and git records when.
    stamp = (f"{prefix} cfg={fingerprint} "
             f"parity={parity} tempo={config.TEMPO_BPM} "
             f"weather={'+'.join(weather)} sieve={config.INSTRUMENT_CONFIGS[0]['sieve']}")
    print(f"\n  provenance stamped on every track: cfg={fingerprint}")

    names = [f"{prefix}_{n}_prime" for n in periods] + [f"{prefix}_arrangement",
                                                        f"{prefix}_ensemble"]
    clear_our_outputs(names)

    print()
    arrangement, merged = [], []
    for channel, voice in enumerate(voices):
        name = voice.name
        notes_per_step = voice.notes
        velocities = voice.velocities
        step_ticks = voice.step_ticks
        line = f"{stamp} voice={name} accents={'+'.join(voice.accents)}"
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


def prepare_accents(field, note_layers, source):
    """Every voice's accents, the piece's one velocity table, and the velocities.

    All of it computed ONCE. Velocity depends on the accent state and never on pitch,
    so the pitch modes share this entirely — they are one piece heard different ways.
    """
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
    describe_accents(fields, note_layers, levels)
    return fields


def main():
    """The whole process, in order. Every pitch mode is rendered from one rhythm."""
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)

    base_binaries, note_layers = derive_note_layers()
    units = {cfg['name']: get_step_ticks(cfg) for cfg in config.INSTRUMENT_CONFIGS}
    parity = parity_point(note_layers, units)

    # THE WEATHER, derived from the sieve unless config names one: one accent per
    # modulus the sieve uses, on the residues that sieve favours. Everything the
    # velocity table is built from therefore comes from the sieve, for any sieve.
    first = config.INSTRUMENT_CONFIGS[0]
    weather = config.WEATHER or derive_weather(base_binaries[first['name']],
                                               first['sieve'], note_layers)
    print("\nWeather " + ("(from config)" if config.WEATHER else "(derived from the sieve)")
          + ": " + ", ".join(f"{k} = {v}" for k, v in weather.items()))

    def field(cfg, residue_source):
        return accent_field(cfg, base_binaries, note_layers, units, parity, weather,
                            residue_source)

    # THE SPAN ACCENT's residues, searched unless config names them.
    if config.SPAN_RESIDUE_SOURCE:
        source = tuple(config.SPAN_RESIDUE_SOURCE)
        print(f"  span residues (from config): {source}")
    else:
        source, reached, target = derive_span_residues(field, note_layers, len(weather) + 1)
        print(f"  span residues (derived): {source} — every pass distinct, "
              + (f"all {target} accent states reached" if reached == target else
                 f"{reached} of {target} accent states reached; the rest never sound"))

    fields = prepare_accents(field, note_layers, source)
    if '--suggest-span' in sys.argv:
        report_span_suggestion(fields, note_layers, source,
                               not config.SPAN_RESIDUE_SOURCE)
        return
    require_distinct_passes(fields, note_layers, source)

    periods = {name: len(f['velocities']) * units[name] for name, f in fields.items()}
    total_ticks = math.lcm(*periods.values())
    print("\n  Voice periods (one full statement at that voice's basic unit):")
    for name, f in fields.items():
        print(f"    {name}: {len(f['velocities'])} steps x {units[name]} ticks "
              f"= {periods[name]}")
    print(f"  Ensemble {total_ticks} ticks — "
          + ", ".join(f"{n} x{total_ticks // p}" for n, p in periods.items()))
    meters, ensemble_meter = choose_meters(note_layers, periods, units, total_ticks)

    # EVERY pitch mode is checked before ANY of them writes. Rendering them in turn and
    # checking each as it came meant a mode that could not render left the earlier
    # modes' files already replaced and the run dead on an exception.
    described = {mode: MODES[mode][1](note_layers) for mode in config.PITCH_MODES}

    failed = []
    for mode in config.PITCH_MODES:
        notes_for, _ = MODES[mode]
        print(f"\n{'=' * 70}\nPitch mode {mode!r}: {described[mode]}")
        voices = build_voices(fields, notes_for, note_layers)
        write_files(voices, periods, total_ticks, meters, ensemble_meter, parity,
                    f"{config.TITLE}_{mode}", weather)
        if not verify(voices, periods, total_ticks, note_layers, base_binaries,
                      f"{config.TITLE}_{mode}", mode, weather):
            failed.append(mode)

    if failed:
        print(f"\n  {', '.join(failed)} FAILED verification")
        sys.exit(1)


if __name__ == '__main__':
    main()
