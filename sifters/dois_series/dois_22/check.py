"""Reading the rendered files back, and proving they are what was intended.

Nothing here trusts the renderer. Every check re-reads the MIDI that was actually
written and tests it against the config, so a fault in the code that writes the notes
cannot vouch for itself.

`verify` is the driver: it runs each `check_*` below, collects every failure rather
than stopping at the first, and prints what it found. Each check is named for the
promise it keeps, and they are independent — read any one on its own.
"""
import os

import mido
import numpy as np

from config import *
from sieve import evaluate, minimal_period, sources_for, RELATIONSHIPS
from midi import read_track, rhythm_from_file, track_meta, gate_ticks


def check_derivations(base_binaries):
    """Assert every voice really is what config says it is derived from.

    This is the one class of error the file-level checks cannot see. Change
    `shift_amount` to 14, or swap `intersection` for `union`, and every clip is still
    one true period, still ends on a bar line, still matches its ensemble track — and
    the piece is no longer the structure it claims to be. The project's whole premise
    is that voices are DERIVED rather than independently authored, so the derivations
    are what must be checked.
    """
    problems = []
    for cfg in INSTRUMENT_CONFIGS:
        name = cfg['name']
        got = base_binaries[name]
        if 'sieve' in cfg:
            want = evaluate(cfg['sieve'], len(got))
            if not np.array_equal(got, want):
                problems.append(f"{name}: does not match its own sieve expression")
            continue

        derives_from = cfg['derives_from']
        if isinstance(derives_from, str):
            derives_from = [derives_from]
        sources = sources_for(cfg, base_binaries)
        want = RELATIONSHIPS[cfg['relationship']](sources, cfg)
        want = want[:minimal_period(want)]
        rel = cfg['relationship']
        if not np.array_equal(got, want):
            problems.append(f"{name}: is not the {rel} of {derives_from}")
            continue

        # The relationships also carry structural promises worth stating outright.
        if rel == 'complement':
            src = tile_to(sources[0], len(got)) if len(sources[0]) != len(got) else sources[0]
            if (got & src).any():
                problems.append(f"{name}: overlaps {derives_from[0]}, so it is not a complement")
            if not (got | src).all():
                problems.append(f"{name}: with {derives_from[0]} leaves gaps; a complement "
                                f"pair must cover every step")
        elif rel == 'shift':
            if cfg['shift_amount'] % len(got) == 0:
                problems.append(f"{name}: shift of {cfg['shift_amount']} is a whole number "
                                f"of periods — it is a copy, not a canon")
        elif rel == 'intersection':
            if not got.any():
                problems.append(f"{name}: the intersection is empty — the voice is silent")
    return problems


def check_parity(check, periods):
    """Every voice ends together — the first moment all of them converge.

    Not a preference: "all voices begin and end together" plus "nothing repeats
    identically" jointly require it. If periods differed, the cycle where they aligned
    would be their LCM, longer than the shortest voice, which would repeat inside it.
    """
    spans = set(periods.values())
    check(len(spans) == 1,
          f"voices do not share a period: {periods}. The ensemble would then be their "
          f"LCM and the shorter voices would repeat inside it.")
    if len(spans) == 1:
        print(f"  parity: every voice is {spans.pop()} ticks")


def check_weather_is_shared(check):
    """Every voice carries the same weather, and differs only in its span accent."""
    sets = {cfg['name']: set(cfg['accent_dict']) for cfg in INSTRUMENT_CONFIGS}
    common = set.intersection(*sets.values())
    for name, own in sets.items():
        check(set(WEATHER) <= own, f"{name}: missing shared weather {set(WEATHER) - own}")
        extra = own - set(WEATHER)
        check(len(extra) == 1,
              f"{name}: carries {len(extra)} accents outside the weather ({extra}); "
              f"only the span accent may differ")
    print(f"  one weather: {sorted(common)} shared by all; "
          f"span accent differs by grid ({', '.join(sorted(n + '=' + next(iter(s - set(WEATHER))) for n, s in sets.items()))})")


def check_weather_in_the_files(check, voices):
    """Principle III, made checkable from the bytes.

    Voices sharing a grid read the same accent field at the same step and rank it with
    the same table, so wherever two of them strike together they must carry the SAME
    velocity. dois_12-dois_17 fail this: the field was rolled for a canon voice, and A
    and C agreed at only 10 of their 80 shared attacks.
    """
    by_grid = {}
    for name, _, _, unit in voices:
        by_grid.setdefault(unit, []).append(name)
    for unit, group in sorted(by_grid.items()):
        at = {n: {o // unit: v for o, _, _, v in read_track(
                  os.path.join(OUTPUT_DIR, f"{TITLE}_{n}_prime.mid"))[0]} for n in group}
        for i, one in enumerate(group):
            for other in group[i + 1:]:
                shared = sorted(set(at[one]) & set(at[other]))
                if not shared:
                    continue
                clash = [t for t in shared if at[one][t] != at[other][t]]
                check(not clash,
                      f"{one} and {other} share the {unit}-tick grid but differ in velocity "
                      f"at {len(clash)} of {len(shared)} shared attacks — they are not under "
                      f"one weather")
                if not clash:
                    print(f"  one weather holds: {one} and {other} agree at all "
                          f"{len(shared)} attacks they share on the {unit}-tick grid")


def check_no_absolute_repetition(check, voices, note_layers):
    """No two passes of a voice's note layer may be identical.

    The minimal-period check in `check_voice_file` catches repetition at a divisor of
    the span, but two arbitrary passes could still coincide without making the whole
    sequence periodic. Compare every pass against every other.
    """
    for name, _, velocities, _ in voices:
        layer = note_layers[name]
        n_passes = len(velocities) // layer
        passes = [tuple(velocities[i * layer:(i + 1) * layer]) for i in range(n_passes)]
        dupes = [(i + 1, j + 1) for i in range(n_passes) for j in range(i + 1, n_passes)
                 if passes[i] == passes[j]]
        check(not dupes,
              f"{name}: passes {dupes} of the note layer are identical — the accent "
              f"field failed to inflect them, so the repetition parity requires is bare")
        if not dupes:
            print(f"  {name}: {n_passes} passes of its note layer, all distinct")


def check_voice_file(check, name, step_ticks, steps, periods, note_layers, base_binaries):
    """One voice's own file: length, articulation, grid, pitch, and its rhythm."""
    path = os.path.join(OUTPUT_DIR, f"{TITLE}_{name}_prime.mid")
    (nm, sig, tempo, end), = track_meta(path)
    notes, hanging, overlaps = read_track(path)

    check(end == periods[name],
          f"{name}: file is {end} ticks, its period is {periods[name]}")
    check(not hanging, f"{name}: {len(hanging)} hanging note(s)")
    check(not overlaps, f"{name}: {len(overlaps)} same-pitch overlap(s)")
    gate = gate_ticks(step_ticks)
    check(all(d == gate for _, d, _, _ in notes),
          f"{name}: not every note is {gate} ticks (gate) long")

    # Notes may abut (gate 1.0) but must never OVERLAP — an overlapping pair is a
    # second Note On for a sounding pitch, which no device handles predictably.
    seq = sorted((o, o + d) for o, d, _, _ in notes)
    overlapping = [(a, b) for (_, a), (b, _) in zip(seq, seq[1:]) if a > b]
    check(not overlapping,
          f"{name}: {len(overlapping)} note(s) start before the previous ends")
    abutting = sum(1 for (_, a), (b, _) in zip(seq, seq[1:]) if a == b)
    if abutting:
        print(f"     {name}: {abutting} consecutive pair(s) abut (gate {GATE_RATIO}) — "
              f"correct, but a device that will not retrigger from a zero-length gap "
              f"needs GATE_RATIO below 1.0")

    check(all(o % step_ticks == 0 for o, _, _, _ in notes),
          f"{name}: some onsets are off the {step_ticks}-tick grid")

    # Pitch is STATIC: every note of a voice is its one configured note, read from the
    # FILE. If pitch ever moves again, this is the check that has to change with it.
    wanted = {c['name']: c['pitch'] for c in INSTRUMENT_CONFIGS}[name]
    sounded = {p for _, _, p, _ in notes}
    check(sounded == {wanted},
          f"{name}: should sound only pitch {wanted}, found {sorted(sounded)}")
    check(min(v for _, _, _, v in notes) >= MIN_VELOCITY,
          f"{name}: a hit has velocity below {MIN_VELOCITY}; MIDI reads velocity 0 "
          f"as a note-off, so the note would vanish rather than sound")

    # The rendered rhythm must be the note layer the sieve actually produces.
    layer, periodic = rhythm_from_file(path, step_ticks, note_layers[name])
    check(periodic,
          f"{name}: onsets are not periodic on its {note_layers[name]}-step note layer")
    if periodic:
        check(np.array_equal(layer, base_binaries[name]),
              f"{name}: the rendered rhythm is not the sieve's note layer")

    bar = sig[0] * (4 * TICKS_PER_QUARTER_NOTE) // sig[1]
    check(end % bar == 0,
          f"{name}: {end} ticks is not whole bars of {sig[0]}/{sig[1]} — host will pad")
    check(tempo == mido.bpm2tempo(TEMPO_BPM), f"{name}: tempo is not {TEMPO_BPM} BPM")

    # The file must be ONE period: not a repeat of something shorter, not a cut.
    grid = [0] * (end // step_ticks)
    for onset, _, _, vel in notes:
        grid[onset // step_ticks] = vel
    measured = minimal_period(grid)
    check(measured == steps[name],
          f"{name}: file spans {steps[name]} steps but the pattern repeats every "
          f"{measured} — it is {steps[name] // measured} copies, not one period")
    print(f"  {name}: {len(notes):>3} notes, {end} ticks, {steps[name]} steps, "
          f"{sig[0]}/{sig[1]}, minimal period {measured}")


def check_ensemble_files(check, voices, periods, total_ticks):
    """The arrangement and ensemble must be whole cycles of the per-voice files."""
    arrangement = os.path.join(OUTPUT_DIR, f"{TITLE}_arrangement.mid")
    ensemble = os.path.join(OUTPUT_DIR, f"{TITLE}_ensemble.mid")
    index = {nm: i for i, (nm, _, _, _) in enumerate(track_meta(arrangement))}
    channels = {cfg['name']: i for i, cfg in enumerate(INSTRUMENT_CONFIGS)}

    for path in (arrangement, ensemble):
        for nm, sig, tempo, end in track_meta(path):
            check(end == total_ticks,
                  f"{os.path.basename(path)} track {nm!r}: {end} ticks, expected {total_ticks}")
            bar = sig[0] * (4 * TICKS_PER_QUARTER_NOTE) // sig[1]
            check(end % bar == 0,
                  f"{os.path.basename(path)} track {nm!r}: not whole bars")

    for name, _, _, _ in voices:
        own, _, _ = read_track(os.path.join(OUTPUT_DIR, f"{TITLE}_{name}_prime.mid"))
        arr, _, _ = read_track(arrangement, track_index=index[name])
        ens, _, _ = read_track(ensemble, channel=channels[name])
        period, reps = periods[name], total_ticks // periods[name]
        check(total_ticks % period == 0, f"{name}: ensemble is not whole cycles")
        for rep in range(reps):
            lo = rep * period
            fold = lambda ns: sorted((o - lo, d, p, v) for o, d, p, v in ns
                                     if lo <= o < lo + period)
            check(fold(arr) == own, f"{name}: arrangement cycle {rep + 1} differs from its file")
            check(fold(ens) == own, f"{name}: ensemble cycle {rep + 1} differs from its file")
        print(f"  {name}: {reps} cycle(s) in both ensemble files, each identical to its file")


def check_velocity_table_is_shared(check, voices, periods):
    """One combination of accents means one velocity, in every voice. New in dois_22.

    Read from the files: for each sounding step, work out which accents were firing
    there and what velocity it was given. Two voices reaching the same accent state must
    have been given the same velocity. Before dois_22 they were not — with the weather
    alone sounding, A played 19 and D played 37, because each voice ranked its own
    accents and D's span accent is common where A's is rare.
    """
    table = {}
    for name, _, _, unit in voices:
        cfg = next(c for c in INSTRUMENT_CONFIGS if c['name'] == name)
        labels = list(cfg['accent_dict'])
        span = periods[name] // unit
        firing = {label: evaluate(expr, span) for label, expr in cfg['accent_dict'].items()}
        notes, _, _ = read_track(os.path.join(OUTPUT_DIR, f"{TITLE}_{name}_prime.mid"))
        for onset, _, _, velocity in notes:
            step = onset // unit
            code = sum(1 << bit for bit, label in enumerate(labels) if firing[label][step])
            table.setdefault(code, {})[name] = velocity
    clashes = {code: by for code, by in table.items() if len(set(by.values())) > 1}
    check(not clashes,
          f"the same accent state means different velocities in different voices: "
          f"{clashes} — the weather is one field, so what it means must be one thing too")
    if not clashes:
        print(f"  one velocity table: {len(table)} accent states reached, "
              f"each meaning one velocity in every voice")


def verify(voices, periods, total_ticks, note_layers, base_binaries):
    """Run every check, collect every failure, and say what was found."""
    failures = []

    def check(condition, message):
        if not condition:
            failures.append(message)
        return condition

    print("\nVerifying the rendered files:")
    steps = {name: len(vel) for name, _, vel, _ in voices}

    failures.extend(check_derivations(base_binaries))
    check_parity(check, periods)
    check_weather_is_shared(check)
    check_weather_in_the_files(check, voices)
    check_velocity_table_is_shared(check, voices, periods)
    check_no_absolute_repetition(check, voices, note_layers)
    if not failures:
        rels = ", ".join(
            f"{c['name']}={c.get('relationship', 'base sieve')}" for c in INSTRUMENT_CONFIGS)
        print(f"  derivations intact: {rels}")

    for name, _, _, step_ticks in voices:
        check_voice_file(check, name, step_ticks, steps, periods, note_layers, base_binaries)
    check_ensemble_files(check, voices, periods, total_ticks)

    if failures:
        print(f"\n  FAILED — {len(failures)} problem(s):")
        for f in failures:
            print(f"    - {f}")
        return False
    print("\n  All checks passed.")
    return True
