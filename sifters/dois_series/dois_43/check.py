"""Reading the rendered files back, and proving they are what was intended."""
import os
import re
from fractions import Fraction

import mido
import numpy as np

import config
from sieve import evaluate, minimal_period, shift_amount, sources_for, tile_to, RELATIONSHIPS
from midi import read_track, rhythm_from_file, track_meta, gate_ticks, output_dir
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
            amount = shift_amount(cfg, config.INSTRUMENT_CONFIGS)
            if amount % len(got) == 0:
                problems.append(f"{name}: shift of {amount} is a whole number "
                                f"of periods — it is a copy, not a canon")
        elif rel == 'intersection':
            if not got.any():
                problems.append(f"{name}: the intersection is empty — the voice is silent")
    return problems


def check_parity(check, periods, parity, voices, note_layers):
    """Every voice ends together, AT THE FIRST convergence — and the accents earn it.

    Two things, and the second is the one that was only implied before.

    All voices must share a period: if they differed, the cycle where they aligned would
    be their LCM, longer than the shortest voice, which would then repeat inside it.

    And that shared period must be the FIRST convergence of the raw rhythms, not some
    later multiple of it. This is what the accents are FOR. Reaching parity across voices
    whose basic durations differ costs repetitions — here A, B and C restate their layer
    four times and D, on a triplet grid, three times — and the span accent exists to make
    those restatements sound different, so the repetition is justified rather than bare.
    Its modulus is derived as the SMALLEST one that spans exactly the repeats parity
    requires: any larger and the piece would run past the convergence, repeating
    something; any smaller and a restatement would go uninflected.

    Checked here because nothing else catches it: an accent whose modulus does not divide
    the note layer inflates the span, and if it inflated every voice's equally the
    voices would still agree with each other while the piece overran its own parity.
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
    """Every voice carries the same weather, and differs only in its span accent."""
    sets = {voice.name: set(voice.accents) for voice in voices}
    common = set.intersection(*sets.values())
    for name, own in sets.items():
        check(set(weather) <= own, f"{name}: missing shared weather {set(weather) - own}")
        extra = own - set(weather)
        check(len(extra) == 1,
              f"{name}: carries {len(extra)} accents outside the weather ({extra}); "
              f"only the span accent may differ")
    print(f"  one weather: {sorted(common)} shared by all; "
          f"span accent differs by grid ({', '.join(sorted(n + '=' + next(iter(s - set(weather))) for n, s in sets.items()))})")


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
                  os.path.join(output_dir(), f"{prefix}_{n}_prime.mid"))[0]} for n in group}
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
    path = os.path.join(output_dir(), f"{prefix}_{name}_prime.mid")
    (nm, sig, tempo, end), = track_meta(path)
    notes, hanging, overlaps = read_track(path)

    check(end == periods[name],
          f"{name}: file is {end} ticks, its period is {periods[name]}")
    check(not hanging, f"{name}: {len(hanging)} hanging note(s)")
    check(not overlaps, f"{name}: {len(overlaps)} same-pitch overlap(s)")
    if config.ARTICULATION == 'held':
        # Held to the voice's next attack, the last to the end of the statement —
        # recomputed from this file's own onsets, not asked of midi.py.
        onsets = sorted(o for o, _, _, _ in notes)
        held = dict(zip(onsets, [b - a for a, b in zip(onsets, onsets[1:] + [end])]))
        check(all(d == held[o] for o, d, _, _ in notes),
              f"{name}: not every note is held until the voice's next attack")
    else:
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
        own, _, _ = read_track(os.path.join(output_dir(), f"{prefix}_{name}_prime.mid"))
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
    """EVERY note's velocity, against the table rebuilt from config. New in dois_23."""
    expected = expected_velocity_table(voices, periods)
    wrong, states_seen = [], set()
    for voice in voices:
        name, unit = voice.name, voice.step_ticks
        labels = list(voice.accents)
        span = periods[name] // unit
        firing = {label: evaluate(expr, span) for label, expr in voice.accents.items()}
        notes, _, _ = read_track(os.path.join(output_dir(), f"{prefix}_{name}_prime.mid"))
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
    """Where a voice's note at a step comes from in its base sieve — rebuilt here.

    pitch.py walks the relationships to write the canon set; this walks them again, its
    own way, so the check is not the writer agreeing with itself.
    """
    by_name = {c['name']: c for c in config.INSTRUMENT_CONFIGS}
    chain, current = [], cfg
    while 'sieve' not in current:
        sources = current['derives_from']
        source = by_name[sources if isinstance(sources, str) else sources[0]]
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
    """What pitch a step should carry, rebuilt here from config.

    `static` is the voice's one note. `lattice` uses multiplication by the diagonal —
    the same map the grid produces, written the other way round, so this check is not
    the renderer agreeing with itself. `canon` is the lattice at each note's origin.
    """
    if mode == 'static':
        note = cfg['pitch']
        return lambda step: note
    period = note_layers[cfg['name']]
    diagonal = lattice_diagonal()      # config-level inputs; the FORMULA below is the
                                       # multiplier form, not the grid the writer used
    if mode == 'canon':
        origin = origin_of(cfg, note_layers)
        return lambda step: config.PITCH_ROOT + (diagonal * origin(step)) % period
    return lambda step: config.PITCH_ROOT + (diagonal * step) % period


def check_canon_imitation(check, voices, prefix, note_layers):
    """In the canon set a shifted voice must play its source's melody, note for note.

    Read from the two written files: every note of C at step n must have the pitch A
    has at step n - 13. And where the two sound together, say what they sound — in the
    lattice set it was always a unison.
    """
    by_name = {c['name']: c for c in config.INSTRUMENT_CONFIGS}
    rendered = {voice.name: voice for voice in voices}
    for voice in voices:
        cfg = by_name[voice.name]
        if cfg.get('relationship') != 'shift' or cfg['derives_from'] not in rendered:
            continue
        source = rendered[cfg['derives_from']]
        shift = shift_amount(cfg, config.INSTRUMENT_CONFIGS)
        own = read_track(os.path.join(output_dir(), f"{prefix}_{voice.name}_prime.mid"))[0]
        theirs = read_track(os.path.join(output_dir(), f"{prefix}_{source.name}_prime.mid"))[0]
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
        name, step_ticks = voice.name, voice.step_ticks
        cfg = next(c for c in config.INSTRUMENT_CONFIGS if c['name'] == name)
        check_voice_file(check, name, step_ticks, steps, periods, note_layers,
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


def read_float_wav(path):
    """(format tag, channels, bits, marker text, samples) — read here, not by the writer.

    The standard library's `wave` module reads only integer PCM, and Serum's wavetables
    are 32-bit float, so this is a separate, minimal RIFF reader: the checker must not
    share the writer's code, or a fault in one could vouch for itself.
    """
    import struct
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
    """The cut order, rebuilt here rather than asked of wavetable.py.

    wavetable.py adds P/m over the moduli. Here the same number is FOUND instead: the one
    residue k with k = P/m (mod m) for every modulus m, by trying them in turn — the
    Chinese-remainder description of the lattice's diagonal. Moduli that share a factor,
    or a k that is not a unit, mean no lattice, and the cuts go in order.
    """
    by_name = {c['name']: c for c in config.INSTRUMENT_CONFIGS}
    moduli, pending = set(), [cfg]
    while pending:
        current = pending.pop()
        if 'sieve' in current:
            moduli.update(int(m) for m in re.findall(r'(\d+)\s*@', current['sieve']))
        else:
            sources = current['derives_from']
            pending += [by_name[n] for n in ([sources] if isinstance(sources, str) else sources)]
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
    """Every frame of every wavetable read back, measured, and matched to the sieve. dois_41.

    Independent of wavetable.py: its own file reader; its own route to the cut order; each
    frame's harmonics rebuilt here from the sieve by the rule they must follow; and the
    sweep's velocities read back out of the rendered MIDI rather than asked of the
    renderer. Checked: the format and a non-factory marker with no blending; 128 frames,
    one per note or velocity value; that frame i sounds exactly the harmonics cut + h for
    which i + h is in the sieve, h = 1 .. P — each at the same strength, the rest silent; that every harmonic starts in the same phase; that every frame has the
    same RMS and the loudest peak in the table is the headroom limit (one gain per table,
    not one per frame); that the sweep plays the frame of each step's velocity and closes
    on its first; and the `.txt` sidecars.
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
        table_rms = inspect(f"{name} table", table_path,
                            [expected_set(rhythm, order, i) for i in range(128)])
        if table_rms is not None:
            peak = np.abs(read_float_wav(table_path)[4]).max()
            if abs(peak - 0.95) > 1e-6:
                failures.append(f"{name} table: loudest peak {peak:.6f}, expected 0.95 — "
                                f"the gain is not set by the table's loudest frame")

        if config.WAVETABLE_SWEEP:
            # The velocities the piece actually plays, read from the written MIDI file.
            span = periods[name] // voice.step_ticks
            midi_path = os.path.join(output_dir(), f"{prefix}_{mode}_{name}_prime.mid")
            notes, _, _ = read_track(midi_path)
            velocity = [0] * span
            for onset, _, _, v in notes:
                velocity[onset // voice.step_ticks] = v
            sweep_path = os.path.join(output_dir(), f"{prefix}_wavetable_{name}_sweep.wav")
            if span + 1 > 256:
                if os.path.exists(sweep_path):
                    failures.append(f"{name}: a sweep table exists for a statement too long "
                                    f"for Serum's 256 frames")
            else:
                wanted = [expected_set(rhythm, order, v) for v in velocity]
                inspect(f"{name} sweep", sweep_path, wanted + wanted[:1], table_rms)

        for path in (table_path,
                     os.path.join(output_dir(), f"{prefix}_wavetable_{name}_sweep.wav")):
            sidecar = os.path.splitext(path)[0] + '.txt'
            if os.path.exists(path) and (not os.path.exists(sidecar) or open(sidecar).read()
                                         != f"[{samples}]\n[no interp]\n"):
                failures.append(f"{os.path.basename(sidecar)}: missing or not "
                                f"'[{samples}]' / '[no interp]'")
    return failures


def check_tuning(prefix, period):
    """The tuning files, read back with parsers of their own. dois_43.

    The `.tun` must give every MIDI note — integer cents under [Tuning], exact under
    [Exact Tuning] — with the root at its usual pitch and `period` steps to the octave;
    the `.scl` the same octave in `period` equal steps; the `.kbm` the root as the scale's
    first degree at its usual frequency.
    """
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
