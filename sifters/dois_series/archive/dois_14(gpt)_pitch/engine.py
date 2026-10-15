"""Add a deterministic pitch field to the existing, independently verified rhythm plan."""
from copy import deepcopy
from dataclasses import dataclass, replace
import hashlib
import json

from . import rhythm_engine
from .rhythm_engine import Note, canonical, integer, minimal_period, validate_grid

ENGINE_VERSION = '2.1.0-pitch'


@dataclass(frozen=True)
class Voice(rhythm_engine.Voice):
    channel: int
    pitch_cycle: tuple
    pitch_derivation: dict


def validate_pitched_voice(voice, parity):
    """Validate the combined sounding pattern, including rests, pitch and velocity."""
    if not voice.pitch_cycle or len(voice.velocities) % len(voice.pitch_cycle):
        raise ValueError(f'{voice.name}: pitch cycle does not close at first parity')
    grid = [None] * len(voice.velocities)
    for note in voice.notes:
        if note.channel != voice.channel or note.onset % voice.unit:
            raise ValueError(f'{voice.name}: wrong channel or off-grid pitched note')
        if not 0 <= note.pitch <= 127 or not 1 <= note.velocity <= 127:
            raise ValueError(f'{voice.name}: invalid pitched MIDI note')
        i = note.onset // voice.unit
        if i >= len(grid) or grid[i] is not None:
            raise ValueError(f'{voice.name}: duplicate or out-of-span pitched onset')
        if note.duration <= 0 or note.onset + note.duration > parity:
            raise ValueError(f'{voice.name}: pitched note extends outside statement')
        if note.pitch != voice.pitch_cycle[i % len(voice.pitch_cycle)]:
            raise ValueError(f'{voice.name}: pitch differs from its field')
        grid[i] = (note.pitch, note.velocity, note.duration)
    validate_grid(tuple(0 if n is None else n[1] for n in grid), voice.layer, voice.name)
    width = len(voice.layer)
    passes = [tuple(grid[i:i + width]) for i in range(0, len(grid), width)]
    if len(set(passes)) != len(passes) or minimal_period(grid) != len(grid):
        raise ValueError(f'{voice.name}: combined pitch/rhythm/velocity pattern repeats')


def gap_field(layer, direction_layer, root):
    """Keep cyclic gap sizes; minimize membership-direction reversals for exact closure."""
    width = len(layer)
    if width > 512:
        raise ValueError('Gap pitch solver supports sieve periods up to 512 steps')
    positions = [i for i, on in enumerate(layer) if on]
    if not positions or len(direction_layer) != width:
        raise ValueError('Gap pitch needs nonempty, equal-period layers')
    gaps = [(positions[(j + 1) % len(positions)] - i) % width or width
            for j, i in enumerate(positions)]
    preferred = [1 if direction_layer[i] else -1 for i in positions]
    # Each reachable sum stores (number of reversals, reversal-bit sequence).
    # Lexicographic ties retain earlier preferred directions. No random seed.
    states = {0: (0, ())}
    for gap, pref in zip(gaps, preferred):
        nxt = {}
        for total, (cost, bits) in states.items():
            for flip in (0, 1):
                target = total + gap * pref * (1 - 2 * flip)
                candidate = (cost + flip, bits + (flip,))
                if target not in nxt or candidate < nxt[target]:
                    nxt[target] = candidate
        states = nxt
    if 0 not in states:
        raise ValueError('Sieve gaps cannot close exactly with signed intervals; change the sieve')
    cost, bits = states[0]
    signs = [pref * (1 - 2 * flip) for pref, flip in zip(preferred, bits)]
    pitch = root + positions[0] % 12
    attack_pitches = []
    for gap, sign in zip(gaps, signs):
        attack_pitches.append(pitch)
        pitch += gap * sign
    assert pitch == attack_pitches[0]
    # Assign pitches to absolute grid positions; rests hold the preceding pitch.
    field = [attack_pitches[-1]] * width
    for j, start in enumerate(positions):
        stop = positions[j + 1] if j + 1 < len(positions) else width
        field[start:stop] = [attack_pitches[j]] * (stop - start)
    return tuple(field), dict(rule='signed cyclic sieve gaps', positions=positions,
                             gaps=gaps, preferred_signs=preferred, signs=signs,
                             direction_reversals=cost, signed_sum=0,
                             attack_pitches=attack_pitches)


def anchor_field(layer, span, root):
    """One class per raw pass, ranked by frequency in this voice's own layer."""
    positions = [i for i, on in enumerate(layer) if on]
    counts = {pc: sum(i % 12 == pc for i in positions) for pc in range(12)}
    ranked = sorted((pc for pc in counts if counts[pc]),
                    key=lambda pc: (-counts[pc], next(i for i in positions if i % 12 == pc)))
    if not ranked:
        raise ValueError('Anchor pitch needs a nonempty sieve')
    cycle = tuple(root + ranked[(i // len(layer)) % len(ranked)] for i in range(span))
    return cycle, dict(rule='intersection pitch-class frequency', counts=counts,
                       ranked_classes=ranked,
                       pass_classes=[cycle[i] - root for i in range(0, span, len(layer))])


def build_plan(settings):
    s = deepcopy(settings)
    if 'PITCH_CONFIG' not in s:
        raise ValueError('PITCH_CONFIG is required')
    pitch_config = s.pop('PITCH_CONFIG')
    base = rhythm_engine.build_plan(s)  # Pitch cannot excuse a repeated accented pass.
    names = {v.name for v in base.voices}
    if not isinstance(pitch_config, dict) or set(pitch_config) != names:
        raise ValueError('PITCH_CONFIG must specify exactly the rendered voices')
    pool = tuple(i for i, selected in enumerate(base.voices[0].layer) if selected)
    source_period = len(base.voices[0].layer)
    voices, used_channels = {}, set()
    for voice, cfg in zip(base.voices, s['INSTRUMENT_CONFIGS']):
        pc = pitch_config[voice.name]
        if not isinstance(pc, dict) or set(pc) != {'root', 'motion', 'channel'}:
            raise ValueError(f'{voice.name}: pitch settings require root, motion, channel')
        root = integer(pc['root'], f'{voice.name} pitch root', 0, 127)
        channel = integer(pc['channel'], f'{voice.name} channel', 1, 16) - 1
        if channel == 9 or channel in used_channels:
            raise ValueError('Pitched voices require distinct channels other than MIDI channel 10')
        used_channels.add(channel)
        motion = pc['motion']
        derivation = {'rule': motion}
        if motion in ('ascending', 'descending', 'slow'):
            period = len(voice.velocities) if motion == 'slow' else source_period
            if len(voice.velocities) % period:
                raise ValueError(f'{voice.name}: pitch period cannot fit first parity')
            indices = [i * len(pool) // period for i in range(period)]
            if motion == 'descending':
                indices = [len(pool) - 1 - i for i in indices]
            cycle = tuple(root + pool[i] for i in indices)
        elif motion == 'gaps':
            direction = next((v for v in base.voices if v.name == 'C'), None)
            if direction is None:
                raise ValueError('Gap direction requires voice C as its membership layer')
            cycle, derivation = gap_field(voice.layer, direction.layer, root)
            derivation['direction_layer'] = 'C'
        elif motion == 'anchors':
            cycle, derivation = anchor_field(voice.layer, len(voice.velocities), root)
        elif motion == 'canon':
            source = cfg.get('derives_from')
            if isinstance(source, list) and len(source) == 1:
                source = source[0]
            if cfg.get('relationship') != 'shift' or not isinstance(source, str) or source not in voices:
                raise ValueError(f'{voice.name}: pitch canon requires a preceding rhythm-shift source')
            parent = voices[source]
            cycle = tuple(root + parent.pitch_cycle[(i - cfg['shift_amount']) % len(parent.pitch_cycle)] - parent.pitch
                          for i in range(len(parent.pitch_cycle)))
        else:
            raise ValueError(f'{voice.name}: unknown pitch motion {motion!r}')
        if min(cycle) < 0 or max(cycle) > 127:
            raise ValueError(f'{voice.name}: pitch field exceeds MIDI range 0–127; adjust its root')
        notes = tuple(replace(n, channel=channel, pitch=cycle[(n.onset // voice.unit) % len(cycle)])
                      for n in voice.notes)
        pitched = Voice(voice.name, root, voice.unit, voice.layer, voice.velocities,
                        voice.accents, voice.phase, voice.levels, notes, channel, cycle, derivation)
        validate_pitched_voice(pitched, base.parity)
        voices[voice.name] = pitched
    # Include every pitch setting and both renderer identities in the fingerprint.
    document = json.loads(base.configuration_json)
    document['PITCH_CONFIG'] = pitch_config
    payload = dict(document, ENGINE_VERSION=ENGINE_VERSION, RHYTHM_ENGINE_VERSION=rhythm_engine.ENGINE_VERSION)
    fingerprint = hashlib.sha256(canonical(payload).encode()).hexdigest()
    return replace(base, voices=tuple(voices.values()), configuration_json=canonical(document), fingerprint=fingerprint)


def diagnostics(plan):
    report = rhythm_engine.diagnostics(plan)
    report['pitch_offsets_semitones'] = [i for i, on in enumerate(plan.voices[0].layer) if on]
    for row, voice in zip(report['voices'], plan.voices):
        row.update(channel=voice.channel + 1, pitch_root=voice.pitch,
                   pitch_derivation=voice.pitch_derivation,
                   pitch_field_steps=len(voice.pitch_cycle),
                   pitch_field_minimal_period_steps=minimal_period(voice.pitch_cycle),
                   used_midi_pitches=sorted({n.pitch for n in voice.notes}))
    return report
