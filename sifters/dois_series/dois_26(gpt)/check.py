"""Reading the rendered files back, and proving they are what was intended."""
import os
from fractions import Fraction

import mido
import numpy as np

import config
from sieve import evaluate, minimal_period, sources_for, RELATIONSHIPS
from midi import read_track, rhythm_from_file, track_meta, gate_ticks
from pitch import lattice_diagonal


def check_derivations(base_binaries):
    """Assert every voice really is what config says it is derived from."""
    problems = []
    for cfg in config.INSTRUMENT_CONFIGS:
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


def check_weather_is_shared(check, voices):
    """Every voice carries the same weather, and differs only in its span accent."""
    sets = {voice.name: set(voice.accents) for voice in voices}
    common = set.intersection(*sets.values())
    for name, own in sets.items():
        check(set(config.WEATHER) <= own, f"{name}: missing shared weather {set(config.WEATHER) - own}")
        extra = own - set(config.WEATHER)
        check(len(extra) == 1,
              f"{name}: carries {len(extra)} accents outside the weather ({extra}); "
              f"only the span accent may differ")
    print(f"  one weather: {sorted(common)} shared by all; "
          f"span accent differs by grid ({', '.join(sorted(n + '=' + next(iter(s - set(config.WEATHER))) for n, s in sets.items()))})")


def check_weather_in_the_files(check, voices, prefix):
    """Principle III, made checkable from the bytes.

    Voices sharing a grid read the same accent field at the same step and rank it with
    the same table, so wherever two of them strike together they must carry the SAME
    velocity. dois_12-dois_17 fail this: the field was rolled for a canon voice, and A
    and C agreed at only 10 of their 80 shared attacks.
    """
    by_grid = {}
    for voice in voices:
        name, unit = voice.name, voice.step_ticks
        by_grid.setdefault(unit, []).append(name)
    for unit, group in sorted(by_grid.items()):
        at = {n: {o // unit: v for o, _, _, v in read_track(
                  os.path.join(config.OUTPUT_DIR, f"{prefix}_{n}_prime.mid"))[0]} for n in group}
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
    for voice in voices:
        name, velocities = voice.name, voice.velocities
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


def check_voice_file(check, name, step_ticks, steps, periods, note_layers,
                     base_binaries, prefix, note_at):
    """One voice's own file: length, articulation, grid, pitch, and its rhythm."""
    path = os.path.join(config.OUTPUT_DIR, f"{prefix}_{name}_prime.mid")
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
        print(f"     {name}: {abutting} consecutive pair(s) abut (gate {config.GATE_RATIO}) — "
              f"correct, but a device that will not retrigger from a zero-length gap "
              f"needs GATE_RATIO below 1.0")

    check(all(o % step_ticks == 0 for o, _, _, _ in notes),
          f"{name}: some onsets are off the {step_ticks}-tick grid")

    # Every note must carry the pitch its step earns, recomputed here rather than
    # asked of pitch.py — for the lattice that means the MULTIPLIER form, a different
    # formula from the one that wrote the notes, so a fault cannot vouch for itself.
    off_pitch = [(o, p) for o, _, p, _ in notes if p != note_at(o // step_ticks)]
    check(not off_pitch,
          f"{name}: {len(off_pitch)} note(s) not at the pitch their step earns; "
          f"first {off_pitch[:3]}")
    check(min(v for _, _, _, v in notes) >= config.MIN_VELOCITY,
          f"{name}: a hit has velocity below {config.MIN_VELOCITY}; MIDI reads velocity 0 "
          f"as a note-off, so the note would vanish rather than sound")

    # The rendered rhythm must be the note layer the sieve actually produces.
    layer, periodic = rhythm_from_file(path, step_ticks, note_layers[name])
    check(periodic,
          f"{name}: onsets are not periodic on its {note_layers[name]}-step note layer")
    if periodic:
        check(np.array_equal(layer, base_binaries[name]),
              f"{name}: the rendered rhythm is not the sieve's note layer")

    bar = sig[0] * (4 * config.TICKS_PER_QUARTER_NOTE) // sig[1]
    check(end % bar == 0,
          f"{name}: {end} ticks is not whole bars of {sig[0]}/{sig[1]} — host will pad")
    check(tempo == mido.bpm2tempo(config.TEMPO_BPM), f"{name}: tempo is not {config.TEMPO_BPM} BPM")

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


def check_ensemble_files(check, voices, periods, total_ticks, prefix):
    """The arrangement and ensemble must be whole cycles of the per-voice files."""
    arrangement = os.path.join(config.OUTPUT_DIR, f"{prefix}_arrangement.mid")
    ensemble = os.path.join(config.OUTPUT_DIR, f"{prefix}_ensemble.mid")
    index = {nm: i for i, (nm, _, _, _) in enumerate(track_meta(arrangement))}
    channels = {cfg['name']: i for i, cfg in enumerate(config.INSTRUMENT_CONFIGS)}

    for path in (arrangement, ensemble):
        for nm, sig, tempo, end in track_meta(path):
            check(end == total_ticks,
                  f"{os.path.basename(path)} track {nm!r}: {end} ticks, expected {total_ticks}")
            bar = sig[0] * (4 * config.TICKS_PER_QUARTER_NOTE) // sig[1]
            check(end % bar == 0,
                  f"{os.path.basename(path)} track {nm!r}: not whole bars")

    for voice in voices:
        name = voice.name
        own, _, _ = read_track(os.path.join(config.OUTPUT_DIR, f"{prefix}_{name}_prime.mid"))
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


def expected_velocity_table(voices, periods):
    """Rebuild the velocity table from config, independently of the renderer."""
    weather_weight, span_weights, order = {}, [], None
    for voice in voices:
        name, unit = voice.name, voice.step_ticks
        labels = list(voice.accents)
        if order is None:
            order = labels[:-1]
        elif labels[:-1] != order:
            raise ValueError(f"{name} orders the weather differently: {labels[:-1]} "
                             f"not {order}")
        span = periods[name] // unit
        for label in labels:
            firing = sum(1 for x in evaluate(voice.accents[label], span) if x)
            rarity = Fraction(span - firing, span)
            if label == labels[-1]:
                span_weights.append(rarity)
            elif weather_weight.setdefault(label, rarity) != rarity:
                raise ValueError(f"weather accent {label!r} is not static: density "
                                 f"differs between voices")
    weights = [weather_weight[label] for label in order] + [max(span_weights)]

    states = range(1 << len(weights))
    by_rarity = sorted(states, key=lambda code: (
        sum(w for bit, w in enumerate(weights) if code >> bit & 1), code))
    reach = config.MAX_VELOCITY - config.MIN_VELOCITY
    return {code: round(config.MIN_VELOCITY + Fraction(reach * rank, len(by_rarity) - 1))
            for rank, code in enumerate(by_rarity)}


def check_every_velocity(check, voices, periods, prefix):
    """EVERY note's velocity, against the table rebuilt from config. New in dois_23."""
    expected = expected_velocity_table(voices, periods)
    wrong, states_seen = [], set()
    for voice in voices:
        name, unit = voice.name, voice.step_ticks
        labels = list(voice.accents)
        span = periods[name] // unit
        firing = {label: evaluate(expr, span) for label, expr in voice.accents.items()}
        notes, _, _ = read_track(os.path.join(config.OUTPUT_DIR, f"{prefix}_{name}_prime.mid"))
        for onset, _, _, velocity in notes:
            step = onset // unit
            code = sum(1 << bit for bit, label in enumerate(labels) if firing[label][step])
            states_seen.add(code)
            if velocity != expected[code]:
                wrong.append((name, onset, code, velocity, expected[code]))
    check(not wrong,
          f"{len(wrong)} note(s) do not carry the velocity their accent state earns; "
          f"first few (voice, onset, state, played, expected): {wrong[:5]}")
    if not wrong:
        print(f"  one velocity table: {len(states_seen)} accent states reached, every "
              f"note of every voice carrying the velocity its state earns")


def expected_note(mode, cfg, note_layers):
    """What pitch a step should carry, rebuilt here from config.

    `static` is the voice's one note. `lattice` uses multiplication by the diagonal —
    the same map the grid produces, written the other way round, so this check is not
    the renderer agreeing with itself.
    """
    if mode == 'static':
        note = cfg['pitch']
        return lambda step: note
    period = note_layers[cfg['name']]
    diagonal = lattice_diagonal()      # config-level inputs; the FORMULA below is the
                                       # multiplier form, not the grid the writer used
    return lambda step: config.PITCH_ROOT + (diagonal * step) % period


def verify(voices, periods, total_ticks, note_layers, base_binaries, prefix, mode):
    """Run every check, collect every failure, and say what was found."""
    failures = []

    def check(condition, message):
        if not condition:
            failures.append(message)
        return condition

    print("\nVerifying the rendered files:")
    steps = {voice.name: len(voice.velocities) for voice in voices}

    failures.extend(check_derivations(base_binaries))
    check_parity(check, periods)
    check_weather_is_shared(check, voices)
    check_weather_in_the_files(check, voices, prefix)
    check_every_velocity(check, voices, periods, prefix)
    check_no_absolute_repetition(check, voices, note_layers)
    if not failures:
        rels = ", ".join(
            f"{c['name']}={c.get('relationship', 'base sieve')}" for c in config.INSTRUMENT_CONFIGS)
        print(f"  derivations intact: {rels}")

    for voice in voices:
        name, step_ticks = voice.name, voice.step_ticks
        cfg = next(c for c in config.INSTRUMENT_CONFIGS if c['name'] == name)
        check_voice_file(check, name, step_ticks, steps, periods, note_layers,
                         base_binaries, prefix, expected_note(mode, cfg, note_layers))
    check_ensemble_files(check, voices, periods, total_ticks, prefix)

    if failures:
        print(f"\n  FAILED — {len(failures)} problem(s):")
        for f in failures:
            print(f"    - {f}")
        return False
    print("\n  All checks passed.")
    return True
