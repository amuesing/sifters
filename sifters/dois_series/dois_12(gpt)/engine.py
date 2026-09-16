"""Configuration -> rhythmic layers -> first-parity plan. No filesystem writes."""
from copy import deepcopy
from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache
import hashlib
import json
import math
import re

import music21
import numpy as np
from . import transformations

ENGINE_VERSION = '1.0.0'


@dataclass(frozen=True, order=True)
class Note:
    onset: int
    duration: int
    channel: int
    pitch: int
    velocity: int


@dataclass(frozen=True)
class Voice:
    name: str
    pitch: int
    unit: int
    layer: tuple
    velocities: tuple
    accents: tuple
    phase: int
    levels: tuple
    notes: tuple


@dataclass(frozen=True)
class Plan:
    title: str
    tpq: int
    tempo: int
    parity: int
    meter: tuple
    voices: tuple
    configuration_json: str
    fingerprint: str


def integer(value, name, minimum=1, maximum=None):
    if type(value) is not int or value < minimum or (maximum is not None and value > maximum):
        raise ValueError(f'{name} must be an integer in {minimum}..{maximum or "unbounded"}')
    return value


def minimal_period(values):
    n = len(values)
    if not n:
        raise ValueError('A periodic layer cannot be empty')
    divisors = sorted({d for i in range(1, math.isqrt(n) + 1) if n % i == 0
                       for d in (i, n // i)})
    return next(p for p in divisors if all(values[i] == values[i % p] for i in range(n)))


def tile(values, span):
    if not values or span <= 0 or span % len(values):
        raise ValueError(f'{span} steps cannot hold whole {len(values)}-step layers')
    return tuple(values) * (span // len(values))


@lru_cache(maxsize=128)
def sieve_layer(expression, limit):
    if not isinstance(expression, str) or not expression.strip():
        raise ValueError('A sieve must be a nonempty expression')
    # Bound the explicit-modulus LCM before music21 constructs its sieve.
    moduli = re.findall(r'(\d+)\s*@', expression)
    if not moduli:
        raise ValueError('Use explicit modulus@residue sieve notation')
    nominal_bound = 1
    for token in moduli:
        modulus = integer(int(token), 'Sieve modulus')
        nominal_bound = math.lcm(nominal_bound, modulus)
        if nominal_bound > limit:
            raise ValueError(f'Sieve period exceeds MAX_STEPS={limit}')
    try:
        obj = music21.sieve.Sieve(expression)
        nominal = int(obj.period())
    except Exception as exc:
        raise ValueError(f'Invalid sieve expression {expression!r}: {exc}') from exc
    if not 1 <= nominal <= limit:
        raise ValueError(f'Sieve period {nominal} exceeds MAX_STEPS={limit}')
    obj.setZRange(0, nominal - 1)
    binary = tuple(int(x) for x in obj.segment(segmentFormat='binary'))
    if len(binary) != nominal or any(x not in (0, 1) for x in binary):
        raise ValueError('Sieve did not produce the requested binary span')
    return binary[:minimal_period(binary)]


def required_modulus(layer, target):
    integer(layer, 'Layer'); integer(target, 'Target')
    if target % layer:
        raise ValueError('Target must contain whole rhythm layers')
    remainder, divisor, modulus = target, 2, 1
    while divisor * divisor <= remainder:
        power = 1
        while remainder % divisor == 0:
            remainder //= divisor
            power *= divisor
        if power > 1 and layer % power:
            modulus *= power
        divisor += 1
    if remainder > 1 and layer % remainder:
        modulus *= remainder
    return modulus


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def config_fingerprint(settings):
    # Ordered weather entries matter for tie-breaking in velocity ranking.
    payload = deepcopy(settings)
    payload['WEATHER'] = list(payload['WEATHER'].items())
    payload['ENGINE_VERSION'] = ENGINE_VERSION
    return hashlib.sha256(canonical(payload).encode()).hexdigest()


def validate_settings(settings):
    s = deepcopy(settings)
    if not isinstance(s['TITLE'], str) or not re.fullmatch(r'[A-Za-z0-9_() -]+', s['TITLE']):
        raise ValueError('TITLE must be a safe filename component')
    integer(s['TICKS_PER_QUARTER_NOTE'], 'TICKS_PER_QUARTER_NOTE', maximum=32767)
    for key in ('MAX_STEPS', 'MAX_EVENTS', 'MAX_VOICES', 'MAX_ACCENTS'):
        integer(s[key], key)
    integer(s['MAX_METER_NUMERATOR'], 'MAX_METER_NUMERATOR', maximum=255)
    integer(s['DRUM_RACK_BASE'], 'DRUM_RACK_BASE', 0, 127)
    integer(s['MIN_VELOCITY'], 'MIN_VELOCITY', 1, 127)
    integer(s['MAX_VELOCITY'], 'MAX_VELOCITY', s['MIN_VELOCITY'] + 1, 127)
    integer(s['UNACCENTED_VELOCITY'], 'UNACCENTED_VELOCITY', 1, 127)
    for key in ('TEMPO_BPM', 'GATE_RATIO'):
        v = s[key]
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v <= 0:
            raise ValueError(f'{key} must be finite and positive')
    if s['GATE_RATIO'] > 1:
        raise ValueError('GATE_RATIO must be in (0, 1]')
    if not 1 <= round(60_000_000 / s['TEMPO_BPM']) <= 0xffffff:
        raise ValueError('TEMPO_BPM cannot be represented in MIDI')
    if s['ACCENT_PHASE_POLICY'] not in ('follow_shift', 'fixed'):
        raise ValueError('ACCENT_PHASE_POLICY must be follow_shift or fixed')
    if s['VELOCITY_POLICY'] != 'per_grid_rarity':
        raise ValueError('Only the explicit per_grid_rarity velocity policy is supported')
    if not isinstance(s['WEATHER'], dict) or len(s['WEATHER']) > s['MAX_ACCENTS']:
        raise ValueError('WEATHER must be a mapping within MAX_ACCENTS')
    for label in s['WEATHER']:
        if not isinstance(label, str) or not label or label.startswith('span'):
            raise ValueError('Weather labels must be nonempty and cannot start with span')
    residues = s['SPAN_RESIDUE_SOURCE']
    if not isinstance(residues, (tuple, list)) or not residues or len(set(residues)) != len(residues):
        raise ValueError('SPAN_RESIDUE_SOURCE must contain distinct nonnegative integers')
    for r in residues:
        integer(r, 'Span residue', 0)
    configs = s['INSTRUMENT_CONFIGS']
    if not isinstance(configs, list) or not 1 <= len(configs) <= s['MAX_VOICES']:
        raise ValueError('Provide at least one voice, within MAX_VOICES')
    known, pads = set(), set()
    allowed = {'name', 'sieve', 'duration', 'step_ticks', 'root', 'derives_from',
               'relationship', 'shift_amount', 'factor'}
    for i, cfg in enumerate(configs):
        if not isinstance(cfg, dict) or set(cfg) - allowed:
            raise ValueError(f'Voice {i}: unknown configuration field')
        name = cfg.get('name')
        if not isinstance(name, str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*', name) or name in known:
            raise ValueError('Voice names must be unique safe identifiers')
        pitch = integer(cfg.get('root', s['DRUM_RACK_BASE'] + i), f'{name} pad', 0, 127)
        if pitch in pads:
            raise ValueError('Each voice must have a distinct Drum Rack pad')
        pads.add(pitch); cfg['root'] = pitch
        if ('duration' in cfg) == ('step_ticks' in cfg):
            raise ValueError(f'{name}: specify exactly one of duration or step_ticks')
        if 'step_ticks' in cfg:
            integer(cfg['step_ticks'], f'{name} step_ticks')
        else:
            if cfg['duration'] not in s['DURATION_MULTIPLIER_KEY']:
                raise ValueError(f'{name}: unknown duration {cfg["duration"]!r}')
            ticks = Fraction(str(s['DURATION_MULTIPLIER_KEY'][cfg['duration']])) * s['TICKS_PER_QUARTER_NOTE']
            if ticks.denominator != 1 or ticks <= 0:
                raise ValueError(f'{name}: duration must resolve to positive integral ticks')
        if 'sieve' in cfg:
            if any(k in cfg for k in ('relationship', 'derives_from', 'factor', 'shift_amount')):
                raise ValueError(f'{name}: use a sieve OR a derivation')
            if i != 0:
                raise ValueError(f'{name}: this iteration derives all voices from the first sieve')
        else:
            rel = cfg.get('relationship')
            if rel not in ('complement', 'retrograde', 'shift', 'augmentation', 'intersection', 'union'):
                raise ValueError(f'{name}: unknown relationship {rel!r}')
            sources = cfg.get('derives_from')
            if isinstance(sources, str):
                sources = [sources]
            if not isinstance(sources, list) or not sources or any(not isinstance(n, str) for n in sources):
                raise ValueError(f'{name}: requires named sources')
            expected = 1 if rel in ('complement', 'retrograde', 'shift', 'augmentation') else 2
            if (expected == 1 and len(sources) != 1) or (expected == 2 and len(sources) < 2) or len(set(sources)) != len(sources):
                raise ValueError(f'{name}: wrong source count for {rel}')
            if any(n not in known for n in sources):
                raise ValueError(f'{name}: sources must be defined before this voice')
            cfg['derives_from'] = sources
            if rel == 'shift':
                if type(cfg.get('shift_amount')) is not int:
                    raise ValueError(f'{name}: shift_amount must be an integer')
            elif 'shift_amount' in cfg:
                raise ValueError(f'{name}: shift_amount only applies to shift')
            if rel == 'augmentation':
                integer(cfg.get('factor'), f'{name} factor')
            elif 'factor' in cfg:
                raise ValueError(f'{name}: factor only applies to augmentation')
        known.add(name)
    return s


def step_ticks(cfg, s):
    return cfg['step_ticks'] if 'step_ticks' in cfg else int(
        Fraction(str(s['DURATION_MULTIPLIER_KEY'][cfg['duration']])) * s['TICKS_PER_QUARTER_NOTE'])


def gate_ticks(unit, ratio):
    return max(1, round(unit * ratio))


def meter_for(bar, s):
    for den in (16, 8, 4, 32, 2, 64, 1):
        numerator = Fraction(bar * den, 4 * s['TICKS_PER_QUARTER_NOTE'])
        if numerator.denominator == 1 and 1 <= numerator <= s['MAX_METER_NUMERATOR']:
            return int(numerator), den
    return None


def choose_meter(parity, bars, s):
    override = s['METER_OVERRIDE']
    if override is not None:
        if not isinstance(override, (list, tuple)) or len(override) != 2:
            raise ValueError('METER_OVERRIDE must be (numerator, denominator)')
        num, den = override
        integer(num, 'Meter numerator', 1, s['MAX_METER_NUMERATOR'])
        integer(den, 'Meter denominator', 1, 128)
        if den & (den - 1):
            raise ValueError('Meter denominator must be a power of two')
        if (Fraction(parity * den, num * 4 * s['TICKS_PER_QUARTER_NOTE'])).denominator != 1:
            raise ValueError('METER_OVERRIDE does not end at a whole bar')
        return num, den
    for bar in sorted(set(bars)):
        if parity % bar == 0 and (meter := meter_for(bar, s)):
            return meter
    if meter := meter_for(parity, s):
        return meter
    raise ValueError('No supported whole-bar meter expresses the first parity; choose an explicit fitting meter')


def validate_grid(grid, layer, name):
    if len(grid) % len(layer):
        raise ValueError(f'{name}: partial rhythm pass')
    if tuple(int(v > 0) for v in grid) != tile(layer, len(grid)):
        raise ValueError(f'{name}: missing or extra rhythmic onsets')
    passes = [tuple(grid[i:i + len(layer)]) for i in range(0, len(grid), len(layer))]
    if len(set(passes)) != len(passes):
        raise ValueError(f'{name}: repeated complete rhythm passes; span accent is not sufficient')
    if minimal_period(grid) != len(grid):
        raise ValueError(f'{name}: rendered pattern has a shorter musical period')


def build_plan(settings):
    s = validate_settings(settings)
    limit = s['MAX_STEPS']
    bases, phases, units = {}, {}, {}
    for cfg in s['INSTRUMENT_CONFIGS']:
        name = cfg['name']; units[name] = step_ticks(cfg, s)
        phase = 0
        if 'sieve' in cfg:
            binary = sieve_layer(cfg['sieve'], limit)
        else:
            sources = [bases[n] for n in cfg['derives_from']]
            common = math.lcm(*(len(x) for x in sources))
            factor = cfg.get('factor', 1)
            if common * factor > limit:
                raise ValueError(f'{name}: transformed layer exceeds MAX_STEPS')
            arrays = [np.array(tile(x, common), dtype=int) for x in sources]
            binary = tuple(int(x) for x in transformations.apply(cfg['relationship'], arrays, cfg))
            binary = binary[:minimal_period(binary)]
            if cfg['relationship'] == 'shift':
                if cfg['shift_amount'] % len(binary) == 0:
                    raise ValueError(f'{name}: a whole-period shift is a copy, not a canon')
                if s['ACCENT_PHASE_POLICY'] == 'follow_shift':
                    phase = phases[cfg['derives_from'][0]] + cfg['shift_amount']
        if not any(binary):
            raise ValueError(f'{name}: silent layers are not supported as rendered voices')
        bases[name] = binary; phases[name] = phase
    parity = math.lcm(*(len(bases[n]) * units[n] for n in bases))
    if any(parity // units[n] > limit for n in bases):
        raise ValueError(f'First parity {parity} ticks exceeds MAX_STEPS per voice')
    weather = {name: sieve_layer(expr, limit) for name, expr in s['WEATHER'].items()}
    # Preflight all weather before constructing full arrays or writing anything.
    for n, layer in bases.items():
        for label, accent in weather.items():
            if len(layer) % len(accent):
                raise ValueError(f'{n}: weather {label} is not static on its {len(layer)}-step layer; first parity cannot be extended')
    estimated = sum(sum(bases[n]) * (parity // units[n] // len(bases[n])) for n in bases)
    if estimated * 6 > s['MAX_EVENTS']:
        raise ValueError('Combined MIDI event count exceeds MAX_EVENTS')
    voices = []
    for cfg in s['INSTRUMENT_CONFIGS']:
        name = cfg['name']; layer = bases[name]; unit = units[name]; span = parity // unit
        modulus = required_modulus(len(layer), span)
        residues = [r for r in s['SPAN_RESIDUE_SOURCE'] if r < modulus]
        if not residues:
            raise ValueError(f'{name}: no source residue fits span modulus {modulus}')
        expression = '|'.join(f'{modulus}@{r}' for r in sorted(residues))
        span_layer = sieve_layer(expression, limit)
        if len(span_layer) != modulus:
            raise ValueError(f'{name}: span residues reduce the required modulus {modulus}')
        accent_defs = tuple(s['WEATHER'].items()) + ((f'span{modulus}', expression),)
        layers = list(weather.values()) + [span_layer]
        if math.lcm(len(layer), *(len(a) for a in layers)) * unit != parity:
            raise ValueError(f'{name}: accent span does not equal first parity')
        states = 1 << len(layers)
        if states > s['MAX_VELOCITY'] - s['MIN_VELOCITY'] + 1:
            raise ValueError('Too many accent states for distinct MIDI velocities')
        rarity = [1 - Fraction(sum(a), len(a)) for a in layers]
        order = sorted(range(states), key=lambda code: (sum(r for i, r in enumerate(rarity) if code >> i & 1), code))
        levels = {code: round(Fraction(s['MIN_VELOCITY']) + Fraction((s['MAX_VELOCITY'] - s['MIN_VELOCITY']) * rank, states - 1))
                  for rank, code in enumerate(order)}
        full = tile(layer, span)  # Transform exactly once, then tile the result.
        grid = tuple(levels[sum(a[(i - phases[name]) % len(a)] << bit for bit, a in enumerate(layers))]
                     if on else 0 for i, on in enumerate(full))
        validate_grid(grid, layer, name)
        notes = tuple(Note(i * unit, gate_ticks(unit, s['GATE_RATIO']), 0, cfg['root'], v)
                      for i, v in enumerate(grid) if v)
        voices.append(Voice(name, cfg['root'], unit, layer, grid, accent_defs, phases[name],
                            tuple(sorted(levels.items())), notes))
    meter = choose_meter(parity, [len(bases[n]) * units[n] for n in bases], s)
    document = deepcopy(s)
    document['WEATHER'] = list(s['WEATHER'].items())
    return Plan(s['TITLE'], s['TICKS_PER_QUARTER_NOTE'], round(60_000_000 / s['TEMPO_BPM']),
                parity, meter, tuple(voices), canonical(document), config_fingerprint(s))
