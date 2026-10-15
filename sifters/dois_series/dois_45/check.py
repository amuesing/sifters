"""Reading the rendered files back, and proving they are what was intended.

Wherever it can, a check recomputes what it tests another way than the writer did (the
lattice as a multiplier, the velocity table from rarities, the wavetables from its own
reader), so a fault in the writer cannot vouch for itself.
"""
import os
import re
import struct
from fractions import Fraction

import mido
import numpy as np

import config
from accents import duplicate_passes
from sieve import (evaluate, minimal_period, shift_amount, sources_for, sources_of, tile_to,
                   RELATIONSHIPS)
from midi import read_track, rhythm_from_file, track_meta, gate_ticks, output_dir
from pitch import lattice_diagonal


def prime_path(prefix, name):
    return os.path.join(output_dir(), f"{prefix}_{name}_prime.mid")


def check_derivations(base_binaries):
    """Every voice really is what config says it is derived from."""
    problems = []
    for cfg in config.INSTRUMENT_CONFIGS:
        name = cfg['name']
        got = base_binaries[name]
        if 'sieve' in cfg:
            if not np.array_equal(got, evaluate(cfg['sieve'], len(got))):
                problems.append(f"{name}: does not match its own sieve expression")
            continue

        derives_from = sources_of(cfg)
        sources = sources_for(cfg, base_binaries)
        want = RELATIONSHIPS[cfg['relationship']](sources, cfg)
        want = want[:minimal_period(want)]
        rel = cfg['relationship']
        if not np.array_equal(got, want):
            problems.append(f"{name}: is not the {rel} of {derives_from}")
            continue

        # The structural promises each relationship makes, stated outright.
        if rel == 'complement':
            src = tile_to(sources[0], len(got)) if len(sources[0]) != len(got) else sources[0]
            if (got & src).any():
                problems.append(f"{name}: overlaps {derives_from[0]}, so it is not a complement")
            if not (got | src).all():
                problems.append(f"{name}: with {derives_from[0]} leaves gaps; a complement "
                                f"pair must cover every step")
        elif rel == 'shift':
            amount = shift_amount(cfg, config.INSTRUMENT_CONFIGS)
            if amount % len(got) == 0:
                problems.append(f"{name}: shift of {amount} is a whole number "
                                f"of periods — it is a copy, not a canon")
        elif rel == 'intersection':
            if not got.any():
                problems.append(f"{name}: the intersection is empty — the voice is silent")
    return problems


def check_parity(check, periods, parity, voices, note_layers):
    """Every voice ends together, at the FIRST convergence, and the accents earn it.

    The span accent is what makes the restatements parity forces sound different, so it
    must span exactly those restatements: more and the piece overruns its own parity,
    repeating something; fewer and a restatement goes uninflected.
    """
    spans = set(periods.values())
    check(len(spans) == 1,
          f"voices do not share a period: {periods}. The ensemble would then be their "
          f"LCM and the shorter voices would repeat inside it.")
    check(spans == {parity},
          f"the voices end at {sorted(spans)} but the first convergence of their raw "
          f"rhythms is {parity}. The accents have stretched the piece past its own "
          f"parity, so something inside it repeats — an accent whose modulus does not "
          f"divide the note layer will do this.")
    for voice in voices:
        layer = note_layers[voice.name]
        needed = parity // (layer * voice.step_ticks)
        rendered = len(voice.velocities) // layer
        check(rendered == needed,
              f"{voice.name}: parity needs {needed} restatements of its {layer}-step "
              f"layer, but the accents span {rendered} — the span accent must justify "
              f"exactly the repeats parity requires, no more and no fewer")
    if spans == {parity}:
        print(f"  parity: every voice is {parity} ticks — the first convergence; "
              + ", ".join(f"{v.name} justifies {len(v.velocities) // note_layers[v.name]}"
                          f" restatement(s)" for v in voices))


def check_weather_is_shared(check, voices, weather):
    """Every voice carries the same weather and differs only in its span accent."""
    sets = {voice.name: set(voice.accents) for voice in voices}
    common = set.intersection(*sets.values())
    for name, own in sets.items():
        check(set(weather) <= own, f"{name}: missing shared weather {set(weather) - own}")
        extra = own - set(weather)
        check(len(extra) == 1,
              f"{name}: carries {len(extra)} accents outside the weather ({extra}); "
              f"only the span accent may differ")
    spans = ', '.join(sorted(n + '=' + next(iter(s - set(weather))) for n, s in sets.items()))
    print(f"  one weather: {sorted(common)} shared by all; span accent differs by grid ({spans})")


def check_weather_in_the_files(check, voices, prefix):
    """Principle III from the bytes: voices on one grid read the same weather at the same
    step, so wherever two strike together they must carry the SAME velocity."""
    by_grid = {}
    for voice in voices:
        by_grid.setdefault(voice.step_ticks, []).append(voice.name)
    for unit, group in sorted(by_grid.items()):
        at = {n: {o // unit: v for o, _, _, v in read_track(prime_path(prefix, n))[0]}
              for n in group}
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
    """No two passes of a voice's note layer may be identical (Principle IV)."""
    for voice in voices:
        layer = note_layers[voice.name]
        dupes = duplicate_passes(voice.velocities, layer)
        check(not dupes,
              f"{voice.name}: passes {dupes} of the note layer are identical — the accent "
              f"field failed to inflect them, so the repetition parity requires is bare")
        if not dupes:
            print(f"  {voice.name}: {len(voice.velocities) // layer} passes of its note "
                  f"layer, all distinct")


def check_voice_file(check, name, step_ticks, steps, periods, note_layers,
                     base_binaries, prefix, note_at):
    """One voice's own file: length, articulation, grid, pitch, and its rhythm."""
    path = prime_path(prefix, name)
    (nm, sig, tempo, end), = track_meta(path)
    notes, hanging, overlaps = read_track(path)

    check(end == periods[name],
          f"{name}: file is {end} ticks, its period is {periods[name]}")
    check(not hanging, f"{name}: {len(hanging)} hanging note(s)")
    check(not overlaps, f"{name}: {len(overlaps)} same-pitch overlap(s)")
    if config.ARTICULATION == 'held':
        # Held to the voice's next attack, the last to the end: from this file's onsets.
        onsets = sorted(o for o, _, _, _ in notes)
        held = dict(zip(onsets, [b - a for a, b in zip(onsets, onsets[1:] + [end])]))
        check(all(d == held[o] for o, d, _, _ in notes),
              f"{name}: not every note is held until the voice's next attack")
    else:
        gate = gate_ticks(step_ticks)
        check(all(d == gate for _, d, _, _ in notes),
              f"{name}: not every note is {gate} ticks (gate) long")

    # Notes may abut but never OVERLAP: a second Note On for a sounding pitch.
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
    off_pitch = [(o, p) for o, _, p, _ in notes if p != note_at(o // step_ticks)]
    check(not off_pitch,
          f"{name}: {len(off_pitch)} note(s) not at the pitch their step earns; "
          f"first {off_pitch[:3]}")
    check(min(v for _, _, _, v in notes) >= config.MIN_VELOCITY,
          f"{name}: a hit has velocity below {config.MIN_VELOCITY}; MIDI reads velocity 0 "
          f"as a note-off, so the note would vanish rather than sound")

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
    arrangement = os.path.join(output_dir(), f"{prefix}_arrangement.mid")
    ensemble = os.path.join(output_dir(), f"{prefix}_ensemble.mid")
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
        own, _, _ = read_track(prime_path(prefix, name))
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
    """The velocity table rebuilt from each accent's rarity, independently of the writer."""
    weights = expected_accent_weights(voices, periods)
    states = range(1 << len(weights))
    by_rarity = sorted(states, key=lambda code: (
        sum(w for bit, w in enumerate(weights) if code >> bit & 1), code))
    reach = config.MAX_VELOCITY - config.MIN_VELOCITY
    return {code: round(config.MIN_VELOCITY + Fraction(reach * rank, len(by_rarity) - 1))
            for rank, code in enumerate(by_rarity)}


def expected_accent_weights(voices, periods):
    """Each accent's rarity, in bit order, rebuilt from config rather than asked for."""
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
    return [weather_weight[label] for label in order] + [max(span_weights)]


def check_every_velocity(check, voices, periods, prefix):
    """EVERY note's velocity, against the table rebuilt from config."""
    expected = expected_velocity_table(voices, periods)
    wrong, states_seen = [], set()
    for voice in voices:
        name, unit = voice.name, voice.step_ticks
        labels = list(voice.accents)
        span = periods[name] // unit
        firing = {label: evaluate(expr, span) for label, expr in voice.accents.items()}
        notes, _, _ = read_track(prime_path(prefix, name))
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


def origin_of(cfg, note_layers):
    """Where a voice's note at a step comes from in its base sieve, walked here its own
    way rather than asked of pitch.py."""
    by_name = {c['name']: c for c in config.INSTRUMENT_CONFIGS}
    chain, current = [], cfg
    while 'sieve' not in current:
        source = by_name[sources_of(current)[0]]
        chain.append((current, source))
        current = source

    def origin(step):
        for link, source in chain:
            if link['relationship'] == 'shift':
                step = step - shift_amount(link, config.INSTRUMENT_CONFIGS)
            elif link['relationship'] == 'retrograde':
                step = note_layers[source['name']] - 1 - step
            elif link['relationship'] == 'augmentation':
                step = step // link['factor']
        return step
    return origin


def expected_note(mode, cfg, note_layers):
    """The pitch a step should carry, rebuilt from config: for the lattice the
    MULTIPLIER form, not the grid the writer used; for the canon, the lattice at each
    note's origin."""
    if mode == 'static':
        note = cfg['pitch']
        return lambda step: note
    period = note_layers[cfg['name']]
    diagonal = lattice_diagonal()
    if mode == 'canon':
        origin = origin_of(cfg, note_layers)
        return lambda step: config.PITCH_ROOT + (diagonal * origin(step)) % period
    return lambda step: config.PITCH_ROOT + (diagonal * step) % period


def check_canon_imitation(check, voices, prefix, note_layers):
    """In the canon set a shifted voice plays its source's melody note for note, read
    from the two written files; and where they sound together, say what they sound."""
    by_name = {c['name']: c for c in config.INSTRUMENT_CONFIGS}
    rendered = {voice.name: voice for voice in voices}
    for voice in voices:
        cfg = by_name[voice.name]
        if cfg.get('relationship') != 'shift' or cfg['derives_from'] not in rendered:
            continue
        source = rendered[cfg['derives_from']]
        shift = shift_amount(cfg, config.INSTRUMENT_CONFIGS)
        own = read_track(prime_path(prefix, voice.name))[0]
        theirs = read_track(prime_path(prefix, source.name))[0]
        layer = note_layers[source.name]
        their_pitch = {}
        for onset, _, pitch, _ in theirs:
            their_pitch.setdefault((onset // source.step_ticks) % layer, pitch)
        wrong = [onset for onset, _, pitch, _ in own
                 if their_pitch.get((onset // voice.step_ticks - shift) % layer) != pitch]
        check(not wrong,
              f"{voice.name}: {len(wrong)} of {len(own)} notes are not {source.name}'s melody "
              f"{shift} steps later — the canon set is not a canon")
        if not wrong:
            together = {}
            for onset, _, pitch, _ in own:
                together.setdefault(onset, []).append(pitch)
            intervals = {(pitch - p) % layer for onset, _, p, _ in theirs
                         for pitch in together.get(onset, [])}
            print(f"  canon: {voice.name} plays {source.name}'s melody {shift} steps later, "
                  f"all {len(own)} notes; where they sound together the interval is "
                  f"{sorted(intervals)} mod {layer}")


def verify(voices, periods, total_ticks, note_layers, base_binaries, prefix, mode,
           weather, parity):
    """Run every check, collect every failure, and say what was found."""
    failures = []

    def check(condition, message):
        if not condition:
            failures.append(message)
        return condition

    print("\nVerifying the rendered files:")
    steps = {voice.name: len(voice.velocities) for voice in voices}

    failures.extend(check_derivations(base_binaries))
    check_parity(check, periods, parity, voices, note_layers)
    check_weather_is_shared(check, voices, weather)
    check_weather_in_the_files(check, voices, prefix)
    check_every_velocity(check, voices, periods, prefix)
    check_no_absolute_repetition(check, voices, note_layers)
    if not failures:
        rels = ", ".join(
            f"{c['name']}={c.get('relationship', 'base sieve')}" for c in config.INSTRUMENT_CONFIGS)
        print(f"  derivations intact: {rels}")

    for voice in voices:
        cfg = next(c for c in config.INSTRUMENT_CONFIGS if c['name'] == voice.name)
        check_voice_file(check, voice.name, voice.step_ticks, steps, periods, note_layers,
                         base_binaries, prefix, expected_note(mode, cfg, note_layers))
    check_ensemble_files(check, voices, periods, total_ticks, prefix)
    if mode == 'canon':
        check_canon_imitation(check, voices, prefix, note_layers)

    if failures:
        print(f"\n  FAILED — {len(failures)} problem(s):")
        for f in failures:
            print(f"    - {f}")
        return False
    print("\n  All checks passed.")
    return True


# ------------------------------------------------------------------- the wavetables

def read_float_wav(path):
    """(format tag, channels, bits, marker text, samples): a minimal RIFF reader of its
    own, since `wave` reads only integer PCM and the checker must not share the
    writer's code."""
    with open(path, 'rb') as handle:
        blob = handle.read()
    if blob[:4] != b'RIFF' or blob[8:12] != b'WAVE':
        raise ValueError(f"{path} is not a RIFF WAVE file")
    found, at = {}, 12
    while at + 8 <= len(blob):
        tag, size = blob[at:at + 4], struct.unpack('<I', blob[at + 4:at + 8])[0]
        found[tag] = blob[at + 8:at + 8 + size]
        at += 8 + size + size % 2
    tag, channels = struct.unpack('<HH', found[b'fmt '][:4])
    bits = struct.unpack('<H', found[b'fmt '][14:16])[0]
    marker = found.get(b'clm ', b'').rstrip(b'\0').decode('latin1')
    return tag, channels, bits, marker, np.frombuffer(found[b'data'], dtype='<f4')


def expected_frame_order(cfg, period):
    """The cut order, FOUND rather than summed: the one residue k with k = P/m (mod m)
    for every modulus m, the Chinese-remainder description of the lattice's diagonal.
    Moduli sharing a factor, or a k that is not a unit, mean the cuts go in order."""
    by_name = {c['name']: c for c in config.INSTRUMENT_CONFIGS}
    moduli, pending = set(), [cfg]
    while pending:
        current = pending.pop()
        if 'sieve' in current:
            moduli.update(int(m) for m in re.findall(r'(\d+)\s*@', current['sieve']))
        else:
            pending += [by_name[n] for n in sources_of(current)]
    moduli = sorted(moduli)
    product = 1
    for m in moduli:
        product *= m
    if any(np.gcd(a, b) != 1 for i, a in enumerate(moduli) for b in moduli[i + 1:]):
        return 1
    found = [k for k in range(product) if all(k % m == (product // m) % m for m in moduli)]
    if len(found) != 1 or np.gcd(found[0], period) != 1:
        return 1
    return found[0]


def check_wavetables(voices, periods, base_binaries, prefix):
    """Every frame of every wavetable read back, measured, and matched to the sieve.

    Checked: the format, a non-factory marker and no blending; 128 frames; that frame i
    sounds exactly harmonics cut + h for which i + h is in the sieve, each at the same
    strength and starting phase, the rest silent; one RMS across the table, with the
    loudest peak at the headroom limit; that the sweep plays the frame of each step's
    velocity, read from the written MIDI, and closes on its first; and the sidecars.
    """
    failures = []
    samples = config.WAVETABLE_FRAME_SAMPLES
    marker = f"<!>{samples} 00000000 wavetable (www.xferrecords.com)"
    mode = config.PITCH_MODES[0]
    configs = {c['name']: c for c in config.INSTRUMENT_CONFIGS}

    def expected_set(rhythm, order, i):
        period = len(rhythm)
        start = (order * i) % period
        return {start + h for h in range(1, period + 1) if rhythm[(i + h) % period]}

    def inspect(label, path, wanted, table_rms=None):
        """`wanted[k]` is the set of harmonics frame k must sound. Returns the RMS."""
        tag, channels, bits, found, audio = read_float_wav(path)
        if (tag, channels, bits) != (3, 1, 32):
            failures.append(f"{label}: format {tag}, {channels} ch, {bits}-bit; expected "
                            f"format 3, mono, 32-bit float")
            return None
        if found != marker:
            failures.append(f"{label}: marker {found!r}, expected {marker!r}")
        if len(audio) != samples * len(wanted):
            failures.append(f"{label}: {len(audio)} samples, expected {len(wanted)} frames "
                            f"of {samples}")
            return None
        frames = audio.reshape(len(wanted), samples).astype(float)
        spectra = np.fft.rfft(frames, axis=1)
        for k, want in enumerate(wanted):
            mag = np.abs(spectra[k])
            loud = mag.max()
            heard = {h for h in range(1, len(mag)) if mag[h] > 1e-3 * loud}
            if heard != want:
                failures.append(f"{label} frame {k}: sounds harmonics {sorted(heard)[:8]}..., "
                                f"the sieve gives {sorted(want)[:8]}...")
                return None
            levels = mag[sorted(want)] / loud
            if levels.min() < 0.999:
                failures.append(f"{label} frame {k}: harmonics not at equal strength "
                                f"(weakest {levels.min():.4f} of the strongest)")
                return None
            phases = np.angle(spectra[k, sorted(want)])
            if np.abs(np.angle(np.exp(1j * (phases + np.pi / 2)))).max() > 1e-3:
                failures.append(f"{label} frame {k}: a harmonic does not start in phase")
                return None
            silent = np.ones(len(mag), dtype=bool)
            silent[sorted(want)] = False
            if mag[silent].max() > 1e-4 * loud:
                failures.append(f"{label} frame {k}: energy outside its period of harmonics")
                return None
        rms = np.sqrt((frames ** 2).mean(axis=1))
        reference = table_rms if table_rms is not None else rms[0]
        if np.abs(rms / reference - 1).max() > 1e-4:
            failures.append(f"{label}: frames differ in level (RMS {rms.min():.5f}-"
                            f"{rms.max():.5f}); one gain must serve the whole table")
            return None
        return reference

    for voice in voices:
        name = voice.name
        rhythm = [int(x) for x in base_binaries[name]]
        order = expected_frame_order(configs[name], len(rhythm))
        table_path = os.path.join(output_dir(), f"{prefix}_wavetable_{name}.wav")
        sweep_path = os.path.join(output_dir(), f"{prefix}_wavetable_{name}_sweep.wav")
        table_rms = inspect(f"{name} table", table_path,
                            [expected_set(rhythm, order, i) for i in range(128)])
        if table_rms is not None:
            peak = np.abs(read_float_wav(table_path)[4]).max()
            if abs(peak - 0.95) > 1e-6:
                failures.append(f"{name} table: loudest peak {peak:.6f}, expected 0.95 — "
                                f"the gain is not set by the table's loudest frame")

        if config.WAVETABLE_SWEEP:
            span = periods[name] // voice.step_ticks
            notes, _, _ = read_track(prime_path(f"{prefix}_{mode}", name))
            velocity = [0] * span
            for onset, _, _, v in notes:
                velocity[onset // voice.step_ticks] = v
            if span + 1 > 256:
                if os.path.exists(sweep_path):
                    failures.append(f"{name}: a sweep table exists for a statement too long "
                                    f"for Serum's 256 frames")
            else:
                wanted = [expected_set(rhythm, order, v) for v in velocity]
                inspect(f"{name} sweep", sweep_path, wanted + wanted[:1], table_rms)

        for path in (table_path, sweep_path):
            sidecar = os.path.splitext(path)[0] + '.txt'
            if os.path.exists(path) and (not os.path.exists(sidecar) or open(sidecar).read()
                                         != f"[{samples}]\n[no interp]\n"):
                failures.append(f"{os.path.basename(sidecar)}: missing or not "
                                f"'[{samples}]' / '[no interp]'")
    return failures


# ------------------------------------------------------------------- the tuning files

def check_tuning(prefix, period):
    """The tuning files, read back with parsers of their own: every MIDI note in both
    sections of the .tun, `period` equal steps closing on 2/1 in the .scl, and the root
    as the first degree at its usual frequency in the .kbm."""
    failures = []
    root = config.PITCH_ROOT
    exact = {n: 100 * root + (n - root) * (1200 / period) for n in range(128)}

    with open(os.path.join(output_dir(), f"{prefix}_tuning.tun")) as handle:
        section, rounded, precise = None, {}, {}
        for line in handle:
            line = line.strip()
            if line.startswith('['):
                section = line
            elif line.startswith('note '):
                n, value = line[5:].split('=')
                (rounded if section == '[Tuning]' else precise)[int(n)] = float(value)
    if sorted(rounded) != list(range(128)) or sorted(precise) != list(range(128)):
        failures.append("tuning .tun: not every MIDI note 0-127 is given in both sections")
    elif any(rounded[n] != round(exact[n]) or abs(precise[n] - exact[n]) > 1e-5
             for n in range(128)):
        failures.append(f"tuning .tun: notes are not {period} equal steps to the octave "
                        f"from MIDI {root}")

    with open(os.path.join(output_dir(), f"{prefix}_tuning.scl")) as handle:
        lines = [x.strip() for x in handle if not x.startswith('!')]
    degrees = lines[2:]
    if int(lines[1]) != period or len(degrees) != period or degrees[-1] != '2/1' or any(
            abs(float(d) - k * 1200 / period) > 1e-5 for k, d in enumerate(degrees[:-1], 1)):
        failures.append(f"tuning .scl: not {period} equal steps closing on 2/1")

    with open(os.path.join(output_dir(), f"{prefix}_tuning.kbm")) as handle:
        fields = [x.strip() for x in handle if not x.startswith('!')]
    hz = 440.0 * 2 ** ((root - 69) / 12)
    if (fields[:5] != ['0', '0', '127', str(root), str(root)]
            or abs(float(fields[5]) - hz) > 1e-4 or fields[6] != str(period)):
        failures.append(f"tuning .kbm: MIDI {root} is not the first degree at {hz:.4f} Hz")
    return failures


# ------------------------------------------------------------------------- the form

def check_form(voices, note_layers, base_binaries, parity, prefix, mode):
    """The form file, rebuilt section by section from each voice's own file.

    In section s a voice is present exactly when its note layer has an attack at step s,
    and then plays its parity statement at the pitches its mode gives step n + s. No two
    sections may be the same.
    """
    failures = []
    path = os.path.join(output_dir(), f"{prefix}_form.mid")
    sections = int(np.lcm.reduce([int(n) for n in note_layers.values()]))
    by_name = {c['name']: c for c in config.INSTRUMENT_CONFIGS}
    meta = track_meta(path)
    if len(meta) != len(voices):
        return [f"form: {len(meta)} tracks, expected one per voice ({len(voices)})"]
    signatures = [[] for _ in range(sections)]
    played = {}
    for index, voice in enumerate(voices):
        name, unit = voice.name, voice.step_ticks
        notes, hanging, overlaps = read_track(path, track_index=index)
        if meta[index][3] != sections * parity:
            failures.append(f"form {name}: ends at {meta[index][3]}, expected "
                            f"{sections} x {parity}")
        if hanging or overlaps:
            failures.append(f"form {name}: hanging or overlapping notes")
        prime = read_track(prime_path(prefix, name))[0]
        pitch_at = expected_note(mode, by_name[name], note_layers)
        binary = base_binaries[name]
        expected = []
        for section in range(sections):
            if not binary[section % len(binary)]:
                continue
            start = section * parity
            expected += [(onset + start, length, pitch_at(onset // unit + section), velocity)
                         for onset, length, _, velocity in prime]
        if sorted(notes) != sorted(expected):
            failures.append(f"form {name}: {len(notes)} notes, expected {len(expected)} — "
                            f"its sections are not its statement, present where its layer "
                            f"has an attack, read {sections} ways")
            continue
        played[name] = sum(int(binary[s % len(binary)]) for s in range(sections))
        for onset, _, pitch, velocity in notes:
            section = onset // parity
            signatures[section].append((name, onset - section * parity, pitch, velocity))
    distinct = len({tuple(sorted(signature)) for signature in signatures})
    if distinct != sections:
        failures.append(f"form: only {distinct} of {sections} sections differ — something "
                        f"repeats identically")
    if not failures:
        print(f"  form: {sections} sections, each voice where its layer has an attack ("
              + ", ".join(f"{n} {k}" for n, k in played.items())
              + f"), each section reading the lattice s steps on; all {sections} differ")
    return failures
