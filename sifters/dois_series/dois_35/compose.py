"""Run the composition: config -> voices -> MIDI files -> checks."""
import hashlib
import itertools
import importlib.metadata
import json
import math
import os
import sys

import config
from sieve import evaluate, build_binary, true_period, voice_rhythm
from accents import (derive_weather, create_accent_binaries, duplicate_passes, notes_for_steps,
                     required_modulus, shared_velocity_levels, span_accent,
                     step_velocities, voice_span)
from midi import (commit_staged, get_step_ticks, make_track, meter_for, staged_output,
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


def state_ceilings(base_binaries, weather, note_layers):
    """The most velocity states each voice could possibly use.

    A voice only sounds where its rhythm has an attack, so it only ever meets the
    weather combinations that occur at those steps. With the span accent free to fire
    or not on each of them, its ceiling is twice that count.

    From dois_35 the weather is CHOSEN so that every voice meets every combination, so
    on this sieve every ceiling is the full table and the search has to reach it. The
    calculation stays because it is what makes that checkable, and because a sieve
    where no weather can manage it is still possible — B was exactly that case until
    dois_34, stuck at six of eight.
    """
    firing = {label: evaluate(expr, max(note_layers.values()))
              for label, expr in weather.items()}
    ceilings = {}
    for name, binary in base_binaries.items():
        combinations = {tuple(bool(firing[label][step]) for label in weather)
                        for step, on in enumerate(binary) if on}
        ceilings[name] = 2 * len(combinations)
    return ceilings


def try_residues(field, note_layers, candidate, levels_only=False):
    """Build every voice with this residue set. Returns (fields, levels) or None."""
    try:
        fields = {c['name']: field(c, candidate, quiet=True)
                  for c in config.INSTRUMENT_CONFIGS}
        levels = shared_velocity_levels({n: f['accents'] for n, f in fields.items()})
    except ValueError:
        return None
    if any(duplicate_passes(velocities_of(f, levels), note_layers[n])
           for n, f in fields.items()):
        return None
    return fields, levels


def weakest_pass_difference(fields, levels, note_layers):
    """How many steps separate the two most SIMILAR passes anywhere in the piece.

    The span accent exists to justify the repetition parity forces, so the measure of
    how well it does that is how different the restatements actually come out. Compare
    every pass of every voice against every other and report the closest pair: one step
    apart means two passes differ by a single note's velocity out of forty, which
    satisfies the letter of Principle IV and almost nothing of its point.
    """
    worst = None
    for name, field in fields.items():
        velocities = list(velocities_of(field, levels))
        layer = note_layers[name]
        passes = [velocities[i * layer:(i + 1) * layer]
                  for i in range(len(velocities) // layer)]
        for one, other in itertools.combinations(passes, 2):
            apart = sum(1 for a, b in zip(one, other) if a != b)
            worst = apart if worst is None else min(worst, apart)
    return worst


def pass_capacity(base_binaries, note_layers, units, parity):
    """How many DIFFERENT accented passes each voice could possibly have.

    A voice restates its note layer to reach parity. The weather is STATIC, so it marks
    the same attacks the same way on every pass; only the span accent varies, and it is
    one binary accent. So a voice with k attacks in its layer has at most 2**k
    distinguishable passes, whatever residues the span accent uses.

    ChatGPT's counting proof, 2026-09-30, and it is worth more than the search it
    replaces: up to dois_31 a sieve that could not work was reported as "no residues
    found", which says nothing about whether any exist. This says none do.

    Necessary, NOT sufficient. Being inside the bound does not make a set reachable —
    periodicity and shared residues cut into it further. Only the failure direction
    proves anything.
    """
    capacity = {}
    for name, layer in note_layers.items():
        attacks = int(base_binaries[name].sum())
        passes = parity // (layer * units[name])
        capacity[name] = (attacks, passes, 2 ** attacks)
    return capacity


def require_pass_capacity(capacity, note_layers, units, parity):
    """Refuse a sieve whose voices cannot have distinct passes, and PROVE it.

    Three different failures used to share one message, which ChatGPT asked to have
    separated (FOR_CLAUDE.md, 2026-09-30):

      1. first convergence — arithmetic, and it always exists;
      2. capacity — this function, a count, and a proof when it fails;
      3. the bounded search and my own selection rules — see `derive_span_residues`,
         which proves nothing about the sieve when it comes up empty.
    """
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


def derive_span_residues(field, note_layers, ceilings, largest, most=5):
    """The span accent's residues: searched, then chosen by how well they do their job.

    Three requirements, in order of what they settle:

      1. no two passes of any voice may be identical — the span accent's whole purpose;
      2. every voice uses every velocity state its own rhythm can reach, which is a
         property of the sieve and narrows the field sharply;
      3. among what survives, keep the set that makes the passes differ MOST.

    The third is new in dois_30 and it matters. Every qualifying set satisfies (1) by
    definition, but satisfying it barely is not the same as satisfying it well: the set
    dois_28 chose, first by number order, left two of B's passes differing at a single
    step out of forty. Maximising the weakest pair turns that into four. Ties go to the
    smaller set, then to the lower residues, so the result stays deterministic.

    The bounds used to be mine: "up to four residues below 16", with no reason behind
    either number. `largest` is now the span accent's own modulus, because `span_accent`
    discards any residue at or above it, so nothing beyond that is even a candidate.
    Measured on the psappha sieve in dois_34: widening 16 to 32 changes NOTHING (the
    same set still wins), but allowing a fifth residue takes the weakest pass pair
    from 4 steps to 6. So `most` was the bound that had been costing something, and 5
    is a choice, not a derivation — the search has to stop somewhere.

    Why the residues cannot simply be read off the sieve the way the weather is: the
    sieve's density at the span modulus is necessarily periodic with gcd(layer, modulus)
    — 8 here, not 32 — so it can never produce a set that spans the modulus. The span
    accent has to be independent of the note layer. That independence is what makes it
    move across the passes, and it is why this one is searched rather than counted.
    """
    best = distinct_only = None
    for size in range(1, most + 1):
        for candidate in itertools.combinations(range(largest), size):
            got = try_residues(field, note_layers, candidate)
            if got is None:
                continue
            fields, levels = got
            used = {n: len({int(v) for v in velocities_of(f, levels) if v})
                    for n, f in fields.items()}
            # Distinctness is Principle IV. The ceiling is MY selection rule. Remember
            # the first set that satisfies the principle, so a refusal can say which of
            # the two actually failed instead of blaming the sieve for both.
            if distinct_only is None:
                distinct_only = (candidate, used)
            if not all(used[n] >= ceilings[n] for n in used):
                continue
            apart = weakest_pass_difference(fields, levels, note_layers)
            if best is None or apart > best[0]:
                best = (apart, candidate, used)
    if best is None:
        raise ValueError(no_residues_message(distinct_only, ceilings, largest, most))
    apart, candidate, used = best
    return candidate, used, apart


def no_residues_message(distinct_only, ceilings, largest, most):
    """Say WHICH requirement the search could not meet, and claim nothing further.

    Two very different failures used to print the same sentence, which told the author
    to change the sieve either way:

      * no candidate made every pass distinct. Principle IV went unmet by this SEARCH.
        Capacity was already checked, so some set may well exist outside these bounds.
      * some candidate did make every pass distinct, and what failed was the rule that
        every voice reach its own state ceiling. That is a selection rule I chose in
        dois_28, not a principle, and the author has said not every state need be used
        by every voice. So name the set that works and let them decide.
    """
    searched = (f"sets of up to {most} residues below {largest}")
    if distinct_only is None:
        return (
            f"no span accent among {searched} made every pass of every voice distinct "
            f"— Principle IV unmet. Every voice is within its accent capacity, so this "
            f"is a failure of THIS bounded search at these basic units and this "
            f"weather, not a proof that no residues exist: a wider search, other units "
            f"or a richer accent design may succeed. Nothing was written.")
    candidate, used = distinct_only
    short = {n: f"{used[n]}/{ceilings[n]}" for n in ceilings if used[n] < ceilings[n]}
    return (
        f"Principle IV is satisfiable — SPAN_RESIDUE_SOURCE = {candidate} makes every "
        f"pass of every voice distinct. What no set among {searched} could also do is "
        f"put every voice at its state ceiling ({short} with that set). That ceiling is "
        f"a selection rule, not a principle. Name those residues in config.py to render "
        f"with them, or widen the search. Nothing was written.")


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


def accent_field(cfg, base_binaries, note_layers, units, parity, weather,
                 residue_source, quiet=False):
    """One voice's accents and its full rhythm. Nothing here knows about pitch.

    The render and the residue search both come through here, so there is no second
    implementation to drift. `residue_source` overrides config's only while searching.
    """
    name = cfg['name']
    label, expression = span_accent(note_layers[name], parity // units[name],
                                    residue_source, quiet)
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
    raise ValueError(
        f"SPAN_RESIDUE_SOURCE = {tuple(source)} leaves identical passes ({bare}), so the "
        f"repetition parity forces would be bare — Principle IV. Nothing was written. "
        f"Run `python3 compose.py --suggest-span` to see how this set does against the "
        f"sieve, or set SPAN_RESIDUE_SOURCE = None and let the search choose.")


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
    return [f"{prefix}_{n}_prime" for n in periods] + [f"{prefix}_arrangement",
                                                       f"{prefix}_ensemble"]


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


def require_static_weather(weather, note_layers):
    """The weather must be STATIC: its period has to divide every note layer.

    `derive_weather` enforces this for the weather it derives, but a weather named in
    config went straight past it until dois_31. A weather that moves against the layer
    stretches the piece past its own parity — a mod-7 accent takes this sieve to 134400
    ticks, 7x parity — and `check.py` only says so once twelve files have been replaced.
    Measured, not nominal: `7@0|7@1|7@2|7@3|7@4|7@5|7@6` calls itself mod 7 and is
    actually constant. Found by ChatGPT in dois_30(gpt).
    """
    for label, expression in weather.items():
        period = true_period(expression, quiet=True)
        against = {name: layer for name, layer in note_layers.items() if layer % period}
        if against:
            raise ValueError(
                f"weather {label!r} = {expression!r} has period {period}, which does not "
                f"divide these note layers: {against}. A weather accent must be static "
                f"within the layer — one that moves is a span accent, and it would push "
                f"the piece past first parity. Nothing was written.")


def require_first_parity(periods, parity):
    """Parity must be the FIRST convergence, checked before anything is replaced.

    check.py asserts this from the written files; this is the same assertion made
    early. With a static weather and a span modulus derived to make the span exactly
    parity I cannot construct a config that reaches this, so treat it as a guard against
    a future change to that derivation rather than a reachable error today. Adopted
    from ChatGPT's dois_30(gpt).
    """
    if set(periods.values()) != {parity}:
        raise ValueError(
            f"voice periods {periods} are not all the first convergence {parity}. The "
            f"accents must span exactly the restatements parity requires, no more and "
            f"no fewer — Principle II. Nothing was written.")


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
    weather = config.WEATHER or derive_weather(base_binaries, first['sieve'],
                                               note_layers)
    print("\nWeather " + ("(from config)" if config.WEATHER else "(derived from the sieve)")
          + ": " + ", ".join(f"{k} = {v}" for k, v in weather.items()))

    require_static_weather(weather, note_layers)

    require_pass_capacity(pass_capacity(base_binaries, note_layers, units, parity),
                          note_layers, units, parity)

    def field(cfg, residue_source, quiet=False):
        return accent_field(cfg, base_binaries, note_layers, units, parity, weather,
                            residue_source, quiet)

    # THE SPAN ACCENT's residues, searched unless config names them.
    ceilings = state_ceilings(base_binaries, weather, note_layers)
    if config.SPAN_RESIDUE_SOURCE:
        source = tuple(config.SPAN_RESIDUE_SOURCE)
        # Report how a NAMED set is doing against the same two measures the search
        # optimises, so pinning the derived answer does not mean flying blind.
        got = try_residues(field, note_layers, source)
        if got is None:
            print(f"  span residues (from config): {source}")
        else:
            got_fields, got_levels = got
            used = {n: len({int(v) for v in velocities_of(f, got_levels) if v})
                    for n, f in got_fields.items()}
            apart = weakest_pass_difference(got_fields, got_levels, note_layers)
            at_ceiling = all(used[n] >= ceilings[n] for n in used)
            print(f"  span residues (from config): {source} — "
                  + ("every voice at its ceiling (" if at_ceiling else "states used (")
                  + ", ".join(f"{n} {used[n]}/{ceilings[n]}" for n in used)
                  + f"); the two most similar passes anywhere differ at {apart} steps")
    else:
        widest = max(required_modulus(note_layers[n], parity // units[n]) or 1
                     for n in note_layers)
        source, used, apart = derive_span_residues(field, note_layers, ceilings, widest)
        print(f"  span residues (derived): {source} — every voice at its ceiling ("
              + ", ".join(f"{n} {used[n]}/{ceilings[n]}" for n in used)
              + f"); the two most similar passes anywhere differ at {apart} steps")

    fields = prepare_accents(field, note_layers, source)
    if '--suggest-span' in sys.argv:
        report_span_suggestion(fields, note_layers, source,
                               not config.SPAN_RESIDUE_SOURCE)
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

    # EVERY pitch mode is checked before ANY of them writes. Rendering them in turn and
    # checking each as it came meant a mode that could not render left the earlier
    # modes' files already replaced and the run dead on an exception.
    described = {mode: MODES[mode][1](note_layers) for mode in config.PITCH_MODES}

    # Everything is rendered and verified in a staging folder, and mid/ is only touched
    # once every mode has passed. Before dois_33 a mode that failed verification had
    # already replaced your files by the time you were told.
    failed, written = [], []
    with staged_output():
        for mode in config.PITCH_MODES:
            notes_for, _ = MODES[mode]
            print(f"\n{'=' * 70}\nPitch mode {mode!r}: {described[mode]}")
            voices = build_voices(fields, notes_for, note_layers)
            written += write_files(voices, periods, total_ticks, meters, ensemble_meter,
                                   parity, f"{config.TITLE}_{mode}", weather)
            if not verify(voices, periods, total_ticks, note_layers, base_binaries,
                          f"{config.TITLE}_{mode}", mode, weather, parity):
                failed.append(mode)

        if failed:
            print(f"\n  {', '.join(failed)} FAILED verification — mid/ is untouched, "
                  f"the files you had are still there")
            sys.exit(1)
        commit_staged(written)


if __name__ == '__main__':
    main()
