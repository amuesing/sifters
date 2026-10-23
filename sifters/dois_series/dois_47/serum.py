"""Serum 2 presets from the sieve: one for every voice, named for its track.

Each rule was worked out and measured in Serum itself in archive/dois_44_studies (percussion.py,
fm_pairs.py; the FM pair at 1:1 is the one the author chose). Here they are part of the
engine, and the presets are written straight in Serum 2's file format, so a render needs
neither Serum nor any library beyond Python's own.

THE DRUM, one rule for every voice; its own rhythm supplies the numbers:
  body      the voice's own wavetable, pitch tracking off
  pitch     the voice's attack rate, KIT_OCTAVES_UP octaves up: its tempo heard as pitch
  decay     the voice's median gap between attacks: each stroke rings until the next
  strike    the pitch falls d/P of an octave over one step, d the lattice's diagonal and P
            its period: 13/40 of an octave, 390 cents, for psappha
  colour    velocity picks the frame, so the accent weather is heard as timbre
  weight    velocity takes the level from KIT_LEVEL up to 1
THE FM PAIR adds a modulator:
  modulator the voice's COMPLEMENT table: every step the voice leaves out, by the same
            table rule. What a voice leaves out modulates what it keeps.
  ratio     1:1, the modulator at the carrier's pitch, following its strike
  depth     an envelope of its own over the median gap, scaled by velocity, so the accent
            weather is heard as brightness

THE FORMAT, read from Serum 2.1.5's own files (undocumented):
  b'XferJson\\0' + uint64 header length + JSON header
  + uint32 payload length + uint32 2 + zstd(payload), the payload the patch as CBOR;
  header['hash'] is the MD5 of the zstd bytes. Every patch starts from Serum's own init
  patch, saved in serum_init.json.

Measured in Serum, not documented: with pitch tracking off the oscillator plays MIDI note
0, 8.18 Hz; NOTE and VELO are mod sources 17 and 16, envelopes 2 and 3 are 3 and 4, and a
second code of 16 scales a source by velocity; a pitch mod amount of 1 moves ~1.2
semitones; a warp amount of 50 is depth 0.5; osc A's 'kFM_OSC' warp takes osc B, which
must be enabled but can be silent; the coarse pitch is continuous.
"""
import copy
import hashlib
import json
import math
import os
import shutil
import statistics
import struct
from compression import zstd

import config
from sieve import ancestral_moduli, diagonal
from wavetable import clear_folder, serum_folder

SERUM_VERSION = ('2.1.5', 11.0)       # the Serum the format and the init patch come from
INIT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'serum_init.json')
MIDI0_HZ = 8.175798915643707          # where a non-tracking oscillator sits
SEMITONES_PER_AMOUNT = 1.2            # measured: pitch moved per unit of mod amount
VELO, ENV2, ENV3_X_VELO = (16, 0), (3, 0), (4, 16)
WT_POS = ('WTOsc', 0, 6, 'kParamTablePos')
WT_POS_B = ('WTOsc', 1, 6, 'kParamTablePos')
WARP = ('WTOsc', 0, 0, 'kParamWarp')
LEVEL = ('Oscillator', 0, 1, 'kParamVolume')
COARSE = ('Oscillator', 0, 6, 'kParamCoarsePit')
COARSE_B = ('Oscillator', 1, 6, 'kParamCoarsePit')
TAGS = ['sifters', 'FM pair', 'Percussion', 'Wavetable']


# ---------------------------------------------------------------- what the sieve gives

def drum(binary, step_seconds):
    """A voice's drum: the numbers its note layer gives the rule above."""
    attacks = [i for i, on in enumerate(binary) if on]
    gaps = [(b - a) % len(binary) or len(binary) for a, b in zip(attacks, attacks[1:] + attacks[:1])]
    rate = len(attacks) / (len(binary) * step_seconds)
    return {'attacks': len(attacks), 'attack_rate_hz': rate,
            'pitch_hz': rate * 2 ** config.KIT_OCTAVES_UP,
            'decay_s': statistics.median(gaps) * step_seconds, 'step_s': step_seconds}


def pitch_controls(hz):
    """OCT, SEM and FINE above MIDI note 0 that reach `hz`."""
    semitones = 12 * math.log2(hz / MIDI0_HZ)
    octave = min(4, int(semitones // 12))
    rest = semitones - 12 * octave
    coarse = int(rest)
    return float(octave), float(coarse), round((rest - coarse) * 100, 2)


def lattice_numbers(cfg):
    """(moduli, diagonal, period) of the sieve a voice descends from."""
    moduli = ancestral_moduli(cfg, config.INSTRUMENT_CONFIGS)
    return moduli, diagonal(moduli), math.prod(moduli)


def strike_cents(cfg):
    """d/P of an octave, or 0 where the sieve has no lattice."""
    _, d, period = lattice_numbers(cfg)
    return 1200 * d / period if d else 0.0


# ------------------------------------------------------------------------- patches

def slot(source, target, amount):
    module, module_id, param_id, name = target
    return {'source': list(source), 'destModuleTypeString': module, 'destModuleID': module_id,
            'destModuleParamID': param_id, 'destModuleParamName': name,
            'plainParams': {'kParamAmount': float(amount)}}


def table_path(title, name):
    """Where Serum finds a table: its labelled folder (`title` is that folder's name)."""
    return f"{config.SERUM_PROJECT}/{title}/{name}.wav"


def drum_patch(init, title, cfg, numbers):
    """The voice's drum on Serum's init patch."""
    voice = cfg['name']
    data = copy.deepcopy(init)
    wt = data['Oscillator0']['WTOsc0']
    wt['relativePathToWT'] = table_path(title, voice)
    wt['numFrames'] = 128 * config.WAVETABLE_FRAME_SAMPLES
    octave, coarse, fine = pitch_controls(numbers['pitch_hz'])
    data['Oscillator0']['plainParams'].update(
        kParamPitchTrack=0.0, kParamOctave=octave, kParamCoarsePit=coarse, kParamFine=fine,
        kParamVolume=config.KIT_LEVEL)
    data['Env0']['plainParams'].update(          # Env 1, the level: one stroke
        kParamAttack=0.0, kParamHold=0.0, kParamDecay=numbers['decay_s'],
        kParamSustain=0.0, kParamRelease=numbers['decay_s'])
    data['Env1']['plainParams'].update(          # Env 2, the strike: one step long
        kParamAttack=0.0, kParamHold=0.0, kParamDecay=numbers['step_s'], kParamSustain=0.0)
    data['ModSlot0'] = slot(VELO, WT_POS, 100.0)
    data['ModSlot1'] = slot(VELO, LEVEL, round(100 * (1 - config.KIT_LEVEL), 6))
    data['ModSlot2'] = slot(ENV2, COARSE, strike_cents(cfg) / 100 / SEMITONES_PER_AMOUNT)
    data['Global0']['plainParams'].update(kParamLimitSameNotePolyphony=1.0)
    return data


def fm_patch(init, title, cfg, numbers):
    """The drum with its complement as an FM modulator at its own pitch."""
    voice = cfg['name']
    data = drum_patch(init, title, cfg, numbers)
    a, b = data['Oscillator0'], data['Oscillator1']
    b['WTOsc1']['relativePathToWT'] = table_path(title, f'not {voice}')
    b['WTOsc1']['numFrames'] = 128 * config.WAVETABLE_FRAME_SAMPLES
    b['plainParams'].update({k: a['plainParams'][k] for k in
                             ('kParamPitchTrack', 'kParamOctave', 'kParamCoarsePit', 'kParamFine')},
                            kParamEnable=1.0, kParamVolume=0.0)
    a['WTOsc0']['plainParams'].update(kParamWarpMenu='kFM_OSC', kParamWarp=0.0)
    data['Env2']['plainParams'].update(          # Env 3, the FM depth: the voice's ring
        kParamAttack=0.0, kParamHold=0.0, kParamDecay=numbers['decay_s'], kParamSustain=0.0)
    data['ModSlot3'] = slot(VELO, WT_POS_B, 100.0)
    data['ModSlot4'] = slot(ENV3_X_VELO, WARP, 100 * config.FM_PEAK_DEPTH)
    # The modulator follows the carrier's strike, so the 1:1 holds through it.
    data['ModSlot5'] = slot(ENV2, COARSE_B, data['ModSlot2']['plainParams']['kParamAmount'])
    return data


# -------------------------------------------------------------------------- format

def _head(major, n):
    if n < 24:
        return bytes([major << 5 | n])
    for code, size, fmt in ((24, 1, '>B'), (25, 2, '>H'), (26, 4, '>I'), (27, 8, '>Q')):
        if n < 1 << (8 * size):
            return bytes([major << 5 | code]) + struct.pack(fmt, n)
    raise ValueError(f"{n} is too large for CBOR")


def cbor(value):
    """CBOR (RFC 8949) for what a Serum patch holds: maps, lists, text, numbers, booleans."""
    if value is True:
        return b'\xf5'
    if value is False:
        return b'\xf4'
    if value is None:
        return b'\xf6'
    if isinstance(value, int):
        return _head(0, value) if value >= 0 else _head(1, -1 - value)
    if isinstance(value, float):
        return b'\xfb' + struct.pack('>d', value)
    if isinstance(value, str):
        data = value.encode('utf-8')
        return _head(3, len(data)) + data
    if isinstance(value, (list, tuple)):
        return _head(4, len(value)) + b''.join(cbor(item) for item in value)
    if isinstance(value, dict):
        return _head(5, len(value)) + b''.join(cbor(k) + cbor(v) for k, v in value.items())
    raise TypeError(f"cannot write {type(value).__name__} into a Serum patch")


def preset_bytes(patch, name, description, tags):
    """A .SerumPreset: the patch with a saved preset's fields, in Serum's container."""
    patch = dict(patch, fileType='SerumPreset', presetName=name, presetAuthor='sifters',
                 presetDescription=description, arpBankDisplayName='', clipBankDisplayName='')
    header = {'fileType': 'SerumPreset', 'presetAuthor': 'sifters',
              'presetDescription': description, 'presetName': name, 'product': 'Serum2',
              'productVersion': SERUM_VERSION[0], 'tags': tags,
              'url': 'https://xferrecords.com/', 'vendor': 'Xfer Records',
              'version': SERUM_VERSION[1]}
    payload = cbor(patch)
    compressed = zstd.compress(payload, level=3)
    header['hash'] = hashlib.md5(compressed).hexdigest()
    text = json.dumps(header, separators=(',', ':')).encode()
    return (b'XferJson\x00' + struct.pack('<Q', len(text)) + text
            + struct.pack('<II', len(payload), 2) + compressed)


# ------------------------------------------------------------------------- writing

def presets_for(base_binaries, units):
    """{name: (patch, description)}, one for every voice: `<folder> <voice>`, the name of
    the track it plays."""
    with open(INIT) as handle:
        init = json.load(handle)
    seconds_per_tick = 60 / (config.TEMPO_BPM * config.TICKS_PER_QUARTER_NOTE)
    families = {'complement': 'its complement', 'shift': 'its canon',
                'intersection': 'their intersection', 'union': 'their union',
                'retrograde': 'its retrograde', 'augmentation': 'its augmentation'}
    title, found = serum_folder(), {}
    for cfg in config.INSTRUMENT_CONFIGS:
        voice = cfg['name']
        numbers = drum(base_binaries[voice], units[voice] * seconds_per_tick)
        what = families.get(cfg.get('relationship'), 'the sieve')
        found[f'{title} {voice}'] = (
            fm_patch(init, title, cfg, numbers),
            f"sifters FM pair, for track {voice} of {config.TITLE}'s MIDI. Voice {voice} "
            f"({what}): its own sieve table at {numbers['pitch_hz']:.1f} Hz (its attack "
            f"rate, {config.KIT_OCTAVES_UP} octaves up), ringing over its median gap "
            f"({numbers['decay_s']:.3f} s), frequency-modulated 1:1 by its complement (not "
            f"{voice}), the FM decaying over the same gap, scaled by velocity; velocity "
            f"picks the frame. Needs Serum's tables under {config.SERUM_PROJECT}/{title}.")
    return found


def presets_folder(presets_root):
    """`Presets/User/<project>/<folder>` inside Serum's presets folder, labelled like the
    tables: `dois_47`."""
    return os.path.join(presets_root, 'Presets', 'User', config.SERUM_PROJECT, serum_folder())


def install_presets(source_dir, filenames, target_dir):
    """Copy the finished presets into Serum's browser, replacing what that one folder
    held, so a preset this render no longer makes cannot linger beside the new ones."""
    parts = os.path.normpath(target_dir).split(os.sep)
    if len(parts) < 4 or parts[-4:-2] != ['Presets', 'User']:
        raise ValueError(f"{target_dir} is not Presets/User/<project>/<version> inside a Serum "
                         f"presets folder; Serum's browser would not list it there")
    clear_folder(target_dir, '.SerumPreset')
    os.makedirs(target_dir, exist_ok=True)
    copied = [name for name in filenames if name.endswith('.SerumPreset')]
    for name in copied:
        shutil.copyfile(os.path.join(source_dir, name), os.path.join(target_dir, name))
    return copied


def write_presets(base_binaries, units, directory):
    """Every preset as `<name>.SerumPreset`. Returns the file names."""
    written = []
    for name, (patch, description) in presets_for(base_binaries, units).items():
        filename = f'{name}.SerumPreset'
        with open(os.path.join(directory, filename), 'wb') as handle:
            handle.write(preset_bytes(patch, name, description, TAGS))
        written.append(filename)
        print(f"  Saved: {filename}  (for track {name.split()[-1]})")
    return written
