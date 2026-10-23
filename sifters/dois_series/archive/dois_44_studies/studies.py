"""Five listening studies on dois_44: the ideas the review raised but did not build.

    python3 studies.py                    # MIDI into mid/, tables into tables/, previews into audio/
    python3 studies.py --install-serum    # also copies the study tables into Serum

Each study borrows dois_44's engine (imported from ../dois_44, never written into) and
changes one thing. README.md says what each one is and marks, plainly, where it departs
from the project's principles. Nothing here is a version of the piece.

  1. a second moving accent — 16 velocity states instead of 8;
  2. orchestration by the sieve's clauses — A and C split by the term that made each attack;
  3. FM wavetables — the step's address on the 8 x 5 grid as ratio and depth, and a
     second table where the voice's own sieve frame is the modulator;
  4. a prolation canon — the sieve at every divisor of its period, all ending together;
  5. four lattice multipliers — x13, x37, x9, x1, one per voice.
"""
import contextlib
import io
import itertools
import json
import math
import shutil
import sys
from fractions import Fraction
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent / 'dois_44'
sys.path.insert(0, str(ENGINE))

import config                                   # noqa: E402  dois_44's settings
import compose                                  # noqa: E402
import wavetable                                # noqa: E402
from accents import (derive_weather, levels_from_weights, notes_for_steps,   # noqa: E402
                     required_modulus)
from midi import make_track, save_tracks, voice_events          # noqa: E402
from pitch import lattice_notes                                  # noqa: E402
from sieve import evaluate, voice_rhythm                         # noqa: E402
from voice import Voice                                          # noqa: E402

import preview                                                   # noqa: E402

MID, TABLES, AUDIO = HERE / 'mid', HERE / 'tables', HERE / 'audio'
config.OUTPUT_DIR = str(MID)            # every file the engine writes lands here
METER = (40, 16)
FIXED_HZ = {'A': 110.0, 'B': 164.81, 'C': 130.81, 'D': 82.41}   # preview only
SUMMARY = {}

CLAUSES = ['(8@0|8@1|8@7)&(5@1|5@3)', '(8@0|8@1|8@2)&5@0', '(8@5|8@6)&(5@2|5@3|5@4)',
           '8@3', '8@4', '8@1&5@2', '8@6&5@1']


# ------------------------------------------------------------------------- the engine

def quietly(function, *args, **kwargs):
    with contextlib.redirect_stdout(io.StringIO()):
        return function(*args, **kwargs)


def engine():
    """dois_44's derivation, unchanged: layers, units, parity, weather, accent fields."""
    base, layers = quietly(compose.derive_note_layers)
    units = {c['name']: compose.get_step_ticks(c) for c in config.INSTRUMENT_CONFIGS}
    parity = math.lcm(*(layers[n] * units[n] for n in layers))
    passes = {n: parity // (layers[n] * units[n]) for n in layers}
    weather = derive_weather(base, config.INSTRUMENT_CONFIGS[0]['sieve'], layers,
                             passes=passes)

    def field(cfg, source, quiet=False):
        return compose.accent_field(cfg, base, layers, units, parity, weather, source, quiet)

    fields = quietly(compose.prepare_accents, field, layers, config.SPAN_RESIDUES)
    return dict(base=base, layers=layers, units=units, parity=parity, weather=weather,
                fields=fields, configs={c['name']: c for c in config.INSTRUMENT_CONFIGS})


def write_set(e, prefix, notes_for, velocities=None):
    """The engine's own six files for one pitch rule: four voices, arrangement, ensemble."""
    voices = []
    for name, field in e['fields'].items():
        vel = field['velocities'] if velocities is None else velocities[name]
        voices.append(Voice(name=name, notes=notes_for_steps(vel, notes_for(name)),
                            velocities=vel, step_ticks=e['units'][name],
                            accents=field['accent_dict']))
    periods = {v.name: e['parity'] for v in voices}
    quietly(compose.write_files, voices, periods, e['parity'], {n: METER for n in periods},
            METER, e['parity'], prefix, e['weather'])
    return voices


def table(path):
    """A wavetable file as (frames, 2048)."""
    data = Path(path).read_bytes()[-128 * 2048 * 4:]          # the data chunk comes last
    return np.frombuffer(data, dtype='<f4').reshape(128, 2048).astype(float)


def reference(mode, voice=None):
    """A file dois_44 already rendered."""
    name = f"dois_44_{mode}_{voice}_prime.mid" if voice else f"dois_44_{mode}_arrangement.mid"
    return ENGINE / 'mid' / name


def wavetable_preview(midi_path, tables, frame_by, loud, out_name):
    """Sound a MIDI file through wavetables, one fixed pitch per track (Serum, tracking off)."""
    events = preview.midi_events(midi_path)
    total = preview.length_of(midi_path) + 0.5
    mix = 0
    for track, name in enumerate('ABCD'):
        own = [ev for ev in events if ev[4] == track]
        if not own:
            continue
        mix = mix + preview.wavetable_voice(own, tables[name], FIXED_HZ[name], frame_by,
                                            loud, total)
    preview.write_wav(AUDIO / out_name, mix)


def tone_preview(midi_path, hz_of, out_name, tracks=None):
    events = preview.midi_events(midi_path)
    total = preview.length_of(midi_path) + 1.0
    preview.write_wav(AUDIO / out_name, preview.tone_voice(
        [ev for ev in events if tracks is None or ev[4] in tracks], hz_of,
        lambda v: 0.25 + 0.75 * v / 127, total))


def pass_differences(velocities, layer):
    passes = [tuple(velocities[i:i + layer]) for i in range(0, len(velocities), layer)]
    return [sum(a != b for a, b in zip(x, y)) for x, y in itertools.combinations(passes, 2)]


# --------------------------------------------- study 1: a second moving accent, 16 states

def second_modulus(layer, span, taken):
    """The smallest modulus that moves against the layer, other than the span accent's own,
    and whose cycle with the layer divides the voice's span — so it never lengthens it."""
    return min(m for m in range(2, span + 1)
               if span % math.lcm(layer, m) == 0 and layer % m and m != taken)


def study_second_accent(e):
    layers, units, parity, weather = e['layers'], e['units'], e['parity'], e['weather']
    spans = {n: parity // units[n] for n in layers}
    rhythm = {n: np.array(e['fields'][n]['rhythm']) for n in layers}
    bits = {n: [np.array(e['fields'][n]['accents'][label]) for label in e['fields'][n]['accents']]
            for n in layers}                                  # mod8, mod5, span — dois_44's
    first = {n: required_modulus(layers[n], spans[n]) for n in layers}
    second = {n: second_modulus(layers[n], spans[n], first[n]) for n in layers}

    def code_with(n, extra):
        return sum((1 << k) * b for k, b in enumerate(bits[n])) + 8 * extra

    def diffs(n, extra):
        code = np.where(rhythm[n] == 1, code_with(n, extra), -1)
        return pass_differences(list(code), layers[n])

    chosen = {}
    for modulus in sorted(set(second.values()), reverse=True):
        names = [n for n in layers if second[n] == modulus]
        blocks = math.gcd(layers[names[0]], modulus)
        size = modulus // blocks
        words = [tuple(1 if q in f else 0 for q in range(size))
                 for f in itertools.combinations(range(size), size // 2)]
        best = None
        for choice in itertools.product(range(len(words)), repeat=blocks):
            residues = tuple(sorted(b + blocks * q for b, w in enumerate(choice)
                                    for q in range(size) if words[w][q]))
            expression = '|'.join(f"{modulus}@{r}" for r in residues)
            key = tuple(sorted(d for n in names
                               for d in diffs(n, np.array(evaluate(expression, spans[n])))))
            if best is None or key > best[0] or (key == best[0] and residues < best[1]):
                best = (key, residues)
        chosen[modulus] = best[1]

    extra = {n: np.array(evaluate('|'.join(f"{second[n]}@{r}" for r in chosen[second[n]]),
                                  spans[n])) for n in layers}
    rarity = lambda arr: Fraction(len(arr) - int(arr.sum()), len(arr))
    weights = ([rarity(bits['A'][k]) for k in range(len(weather))]
               + [max(rarity(bits[n][-1]) for n in layers), max(rarity(extra[n]) for n in layers)])
    levels = levels_from_weights(weights)
    velocities = {}
    for n in layers:
        code = code_with(n, extra[n])
        velocities[n] = np.where(rhythm[n] == 1, [levels[int(c)] for c in code], 0)

    write_set(e, 'study1_second_accent_static',
              lambda n: (lambda step, pad=e['configs'][n]['pitch']: pad), velocities)
    write_set(e, 'study1_second_accent_lattice',
              lambda n: lattice_notes(e['configs'][n], layers), velocities)
    SUMMARY['1'] = {
        'second moduli': {n: second[n] for n in layers},
        'second residues': {str(m): r for m, r in chosen.items()},
        'table': [levels[c] for c in range(16)],
        'states used': {n: len({int(v) for v in velocities[n] if v}) for n in layers},
        'pass differences': {n: [min(diffs(n, extra[n])), max(diffs(n, extra[n]))] for n in layers},
        'dois_44 pass differences': {
            n: [min(pass_differences(list(e['fields'][n]['velocities']), layers[n])),
                max(pass_differences(list(e['fields'][n]['velocities']), layers[n]))]
            for n in layers},
    }


# ------------------------------------------------- study 2: orchestration by clause

def study_clauses(e):
    layers, units, parity = e['layers'], e['units'], e['parity']
    member = [np.array(evaluate(c, 40)) for c in CLAUSES]
    assert (sum(member) == np.array(e['base']['A'])).all(), 'the clauses must partition A'
    clause_of = {n: k for k, m in enumerate(member) for n in np.flatnonzero(m)}
    shift = 13
    pad = {'B': 36 + len(CLAUSES), 'D': 37 + len(CLAUSES)}

    def note_for(name):
        if name == 'A':
            return lambda step: 36 + clause_of[step % 40]
        if name == 'C':                                   # C's attack came from A's at n - 13
            return lambda step: 36 + clause_of[(step - shift) % 40]
        return lambda step: pad[name]

    write_set(e, 'study2_clauses', note_for)
    SUMMARY['2'] = {'clause sizes': [int(m.sum()) for m in member],
                    'pads': 'A and C: 36-42 by clause (C takes the clause of the attack it '
                            'copies); B 43; D 44'}


# ---------------------------------------------------------- study 3: FM wavetables

def fm_frame(modulator, depth, carrier=1, samples=2048):
    t = np.arange(samples) / samples
    return np.sin(2 * np.pi * carrier * t + depth * np.sin(2 * np.pi * modulator * t))


def one_gain(frames):
    gain = wavetable.PEAK / max(np.max(np.abs(f)) for f in frames)
    return [gain * f for f in frames]


def brightness(frame):
    mag = np.abs(np.fft.rfft(frame)) ** 2
    h = np.arange(len(mag))
    return float(np.log2((h * mag).sum() / mag.sum()))


def energy_top(frame, share=0.999):
    """The harmonic below which `share` of a frame's energy lies."""
    power = np.abs(np.fft.rfft(frame)) ** 2
    return int(np.searchsorted(np.cumsum(power) / power.sum(), share))


def deepest_within_two_periods(own, period=40):
    """The deepest phase modulation whose sidebands keep 99.9% of every frame's energy
    below harmonic 2P — the same two-period bound dois_41 puts on the sieve frames, so the
    table still sounds whole at middle C. Found by bisection, not chosen."""
    t = np.arange(own.shape[1]) / own.shape[1]

    def fits(depth):
        return all(energy_top(np.sin(2 * np.pi * t + depth * f / np.max(np.abs(f))))
                   < 2 * period for f in own)

    low, high = 0.0, np.pi
    while high - low > 1e-3:
        middle = (low + high) / 2
        low, high = (middle, high) if fits(middle) else (low, middle)
    return low


def study_fm(e):
    TABLES.mkdir(exist_ok=True)
    grid = one_gain([fm_frame(i % 8 + 1, i % 5 + 1) for i in range(128)])
    wavetable.write_wav(TABLES / 'study3_fm_grid.wav', grid)
    wavetable.write_sidecar(str(TABLES), 'study3_fm_grid.wav')
    sieve_pm, depths = {}, {}
    for name in 'ABCD':
        own = table(ENGINE / 'mid' / f'dois_44_wavetable_{name}.wav')
        depth = deepest_within_two_periods(own)
        depths[name] = round(depth, 3)
        t = np.arange(2048) / 2048
        # the voice's own sieve frame, scaled to +-depth radians, modulates a sine's phase
        frames = one_gain([np.sin(2 * np.pi * t + depth * own[i] / np.max(np.abs(own[i])))
                           for i in range(128)])
        wavetable.write_wav(TABLES / f'study3_pm_sieve_{name}.wav', frames)
        wavetable.write_sidecar(str(TABLES), f'study3_pm_sieve_{name}.wav')
        sieve_pm[name] = frames
    lit = [brightness(f) for f in grid]
    pm = [brightness(f) for f in sieve_pm['A']]
    SUMMARY['3'] = {
        'fm grid': {'distinct frames': len({tuple(np.round(f, 6)) for f in grid}),
                    'brightness range (octaves)': round(max(lit) - min(lit), 2),
                    'neighbours (octaves, median)': round(float(np.median(np.abs(np.diff(lit)))), 2)},
        'pm depth (radians, derived)': depths,
        'pm by sieve (A)': {'distinct frames': len({tuple(np.round(f, 6)) for f in sieve_pm['A']}),
                            'brightness range (octaves)': round(max(pm) - min(pm), 2),
                            'neighbours (octaves, median)': round(float(np.median(np.abs(np.diff(pm)))), 2)},
    }


# ------------------------------------------------------- study 4: a prolation canon

FACTORS = [1, 2, 4, 5, 8, 10, 20, 40]       # every divisor of the period
BASE_TICKS = 60                              # the fastest layer's step: a 32nd note


def study_prolation(e):
    layer = np.array(e['base']['A'])
    total = 40 * BASE_TICKS * 40             # the slowest layer states the sieve once
    weather = e['weather']
    firing = {label: np.array(evaluate(expr, 40)) for label, expr in weather.items()}
    rarity = lambda arr: Fraction(len(arr) - int(arr.sum()), len(arr))
    levels = levels_from_weights([rarity(firing[label]) for label in weather])
    code = sum((1 << k) * firing[label] for k, label in enumerate(weather))
    one_pass = np.where(layer == 1, [levels[int(c)] for c in code], 0)

    for mode in ('static', 'lattice'):
        tracks, merged = [], []
        for index, factor in enumerate(sorted(FACTORS)):
            step = BASE_TICKS * 40 // factor
            velocities = np.tile(one_pass, factor)
            if mode == 'static':
                note_at = lambda n, pad=36 + index: pad
            else:
                note_at = lambda n: 36 + (13 * n) % 40
            notes = notes_for_steps(velocities, note_at)
            events = voice_events(notes, velocities, step, total, channel=index)
            name = f"x{factor}"
            tracks.append(make_track(name, events, total, METER,
                                     f"study4 prolation layer {name}: unit {step} ticks"))
            merged += events
        quietly(save_tracks, tracks, f"study4_prolation_{mode}_arrangement", total, METER)
        quietly(save_tracks, [make_track('prolation', merged, total, METER, 'study4 prolation')],
                f"study4_prolation_{mode}_ensemble", total, METER)
    SUMMARY['4'] = {'layers (statements of the sieve)': FACTORS,
                    'step ticks': [BASE_TICKS * 40 // f for f in sorted(FACTORS)],
                    'length ticks': total, 'seconds at 120 BPM': total / 960,
                    'velocity table (weather only)': [levels[c] for c in range(4)]}


# ------------------------------------------------- study 5: four lattice multipliers

MULTIPLIERS = {'A': 13, 'B': 37, 'C': 9, 'D': 1}     # 13, 13^3, 13^2, 13^4 mod 40


def study_multipliers(e):
    write_set(e, 'study5_multipliers',
              lambda n: (lambda step, k=MULTIPLIERS[n]: 36 + (k * step) % 40))
    layers, units = e['layers'], e['units']
    at = {n: {t: (MULTIPLIERS[n] * (t // units[n])) % 40
              for t in range(0, e['parity'], units[n]) if e['fields'][n]['rhythm'][t // units[n]]}
          for n in layers}
    together = {}
    for x, y in itertools.combinations('ABCD', 2):
        shared = set(at[x]) & set(at[y])
        if shared:
            together[x + y] = {'meetings': len(shared),
                               'unisons': sum(at[x][t] == at[y][t] for t in shared)}
    steps = {n: sorted({(MULTIPLIERS[n] * d) % 40 for d in (1, 2)}) for n in layers}
    SUMMARY['5'] = {'multipliers': MULTIPLIERS, 'meetings': together,
                    'one-step and two-step moves (mod 40)': steps}


# ------------------------------------------------------------------------ previews

def previews(e):
    AUDIO.mkdir(exist_ok=True)
    own = {n: table(ENGINE / 'mid' / f'dois_44_wavetable_{n}.wav') for n in 'ABCD'}
    by_velocity = lambda note, velocity: velocity
    by_note = lambda note, velocity: note
    even = lambda velocity: 0.8
    loud = lambda velocity: 0.35 + 0.65 * velocity / 127

    # 1: velocity -> wavetable position, 8 states against 16
    wavetable_preview(reference('static'), own, by_velocity, even, '1a_dois44_velocity_8_states.wav')
    wavetable_preview(MID / 'study1_second_accent_static_arrangement.mid', own, by_velocity,
                      even, '1b_second_accent_velocity_16_states.wav')
    # 2: note -> wavetable position: one frame per voice, against a frame per clause
    wavetable_preview(reference('static'), own, by_note, loud, '2a_dois44_one_timbre_per_voice.wav')
    wavetable_preview(MID / 'study2_clauses_arrangement.mid', own, by_note, loud,
                      '2b_clauses_a_timbre_per_clause.wav')
    # 3: the lattice set through three tables
    grid = table(TABLES / 'study3_fm_grid.wav')
    pm = {n: table(TABLES / f'study3_pm_sieve_{n}.wav') for n in 'ABCD'}
    wavetable_preview(reference('lattice'), own, by_note, loud, '3a_dois44_additive_table.wav')
    wavetable_preview(reference('lattice'), {n: grid for n in 'ABCD'}, by_note, loud,
                      '3b_fm_grid_table.wav')
    wavetable_preview(reference('lattice'), pm, by_note, loud, '3c_pm_by_sieve_table.wav')
    # 4: the prolation canon, pitched
    tone_preview(MID / 'study4_prolation_lattice_arrangement.mid', preview.twelve_tet(24),
                 '4_prolation_canon.wav')
    # 5: four multipliers against the lattice and canon sets, in 12-TET and 40 steps
    for label, path in (('5a_dois44_lattice', reference('lattice')),
                        ('5b_dois44_canon', reference('canon')),
                        ('5c_four_multipliers', MID / 'study5_multipliers_arrangement.mid')):
        tone_preview(path, preview.twelve_tet(24), f'{label}_12tet.wav')
        tone_preview(path, preview.forty_step(), f'{label}_40step.wav')


def install():
    """The study tables into Serum's `sifters/dois_44 experiments` folder."""
    folder = Path(wavetable.serum_presets_folder()) / 'Tables' / 'sifters' / 'dois_44 experiments'
    folder.mkdir(parents=True, exist_ok=True)
    copied = []
    for path in sorted(TABLES.glob('*.wav')):
        target = path.name.removeprefix('study3_').replace('_', ' ')
        shutil.copyfile(path, folder / target)
        copied.append(target)
    print(f"  {len(copied)} study table(s) in Serum: {folder}")


def main():
    MID.mkdir(exist_ok=True)
    e = engine()
    for study in (study_second_accent, study_clauses, study_fm, study_prolation,
                  study_multipliers):
        study(e)
        print(f"  built {study.__name__}")
    previews(e)
    print(f"  previews in {AUDIO}")
    (HERE / 'summary.json').write_text(json.dumps(SUMMARY, indent=1, default=str))
    if '--install-serum' in sys.argv:
        install()


if __name__ == '__main__':
    main()
