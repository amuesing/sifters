"""FM pairs: each voice frequency-modulated by its own complement, live in Serum 2.

    <python with pedalboard, zstandard, cbor2, mido, numpy, music21> fm_pairs.py

The percussion kit (percussion.py) plays each voice's wavetable as a drum. Here a second
oscillator joins it as an FM modulator, and the sieve decides what it plays:

  modulator   the voice's own COMPLEMENT: a table built from every step the voice does not
              occupy, by the same rule as the voice's own table. What a voice leaves out
              modulates what it keeps. A and B are each other's complement, so they
              modulate each other; C's and D's complements are new tables.
  ratio       modulator : carrier, from the sieve's own numbers: 1:1; 8:5, its two moduli;
              13:1, its lattice diagonal. The modulator follows the carrier's strike.
  depth       an envelope of its own, decaying over the voice's median gap between attacks
              (the same rule as the drum's ring), scaled by velocity: every stroke starts
              bright and settles, and the accent weather is heard as brightness.
  frame       the modulator reads the same frame as the carrier (velocity or note).

Also rendered: the canon set; the lattice set with every note held to its voice's next
attack; eight_five's static set; and BAKED FM (fm_tables.py), a table per voice whose
frame number is the modulation depth (a sine carrier, the voice's own frame as modulator),
swept by the same envelope.

Measured in Serum 2.1.5: on oscillator A, warp `kFM_OSC` takes oscillator B as its
modulator, which must be enabled but can sit at volume 0; a mod slot's amount maps
directly onto warp depth (50 = 0.5); a source written [4, 16] is envelope 3 scaled by
velocity; the coarse pitch is continuous and reaches at least +64 semitones, so any ratio
sits exactly. Below depth ~0.15 the FM is inaudible, so the softest accent state keeps the
plain table. On the kit's one-step strike envelope the FM lasted 15-40 ms, a click, hence
an envelope of its own.

Chosen, not derived: which of the sieve's ratios, the peak depth (1.0 at velocity 127),
and Serum's own FM mode.

Writes: audio_fm/ (renders); tables/fm_not_*.wav and fm_depth_*.wav; presets/fm_pairs/
(every patch as .SerumPreset and .vstpreset); and, because Serum loads tables and lists
presets only from its own folders, Tables/sifters/dois_45 experiments/ and
Presets/User/sifters/FM pairs/ there.
"""
import copy
import json
import math
import shutil
import subprocess
import tempfile
from pathlib import Path

import mido
import numpy as np

import percussion
import serum_render
import serum_state
import wavetable                      # dois_44's, through percussion's path: the same rule as dois_45's
import fm_tables

HERE = Path(__file__).resolve().parent
DOIS_45 = HERE.parent / 'dois_45'
OUT = HERE / 'audio_fm'
TABLES = HERE / 'tables'
PRESETS = HERE / 'presets' / 'fm_pairs'
SERUM_TABLES = 'sifters/dois_45 experiments'
SERUM_PRESETS = Path('Presets') / 'User' / 'sifters' / 'FM pairs'
RATIOS = {'1-1': 1.0, '8-5': 8 / 5, '13-1': 13.0}       # modulator : carrier
PEAK_DEPTH = 100.0                    # chosen: warp depth 1.0 at velocity 127
ENV3_X_VELO = (4, 16)                 # envelope 3, scaled by velocity
WT_POS_A = ('WTOsc', 0, 6, 'kParamTablePos')
WT_POS_B = ('WTOsc', 1, 6, 'kParamTablePos')
WARP_A = ('WTOsc', 0, 0, 'kParamWarp')
COARSE_B = ('Oscillator', 1, 6, 'kParamCoarsePit')
VARIANTS = {'accents': percussion.VELO, 'lattice': percussion.NOTE}


# ------------------------------------------------------------------------- tables

def build_tables():
    """Each voice's complement table and baked depth table, also installed in Serum."""
    rhythms = percussion.voice_rhythms()
    configs = {cfg['name']: cfg for cfg in percussion.config.INSTRUMENT_CONFIGS}
    folder = Path(wavetable.serum_presets_folder()) / 'Tables' / SERUM_TABLES
    folder.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(exist_ok=True)
    deepest = {}
    for voice, (layer, _) in rhythms.items():
        complement = [1 - x for x in layer]
        order = wavetable.frame_order(configs[voice], len(layer))
        wavetable.write_wav(str(TABLES / f'fm_not_{voice}.wav'),
                            wavetable.integer_frames(complement, order))
        frames, deepest[voice] = fm_tables.depth_table(layer, order)
        wavetable.write_wav(str(TABLES / f'fm_depth_{voice}.wav'), frames)
        shutil.copyfile(TABLES / f'fm_not_{voice}.wav', folder / f'not {voice}.wav')
        shutil.copyfile(TABLES / f'fm_depth_{voice}.wav', folder / f'{voice} FM depth.wav')
    print(f"  tables installed in {folder}; baked depth reaches "
          + ", ".join(f"{v} {d:.2f} rad" for v, d in deepest.items()))
    return deepest


# ------------------------------------------------------------------------ patches

def fm_data(kit, voice, numbers, colour, ratio=1.0, held=False):
    """The kit's patch for this voice, with its complement as an FM modulator."""
    data = kit.patch_data(voice, numbers, colour)
    a, b = data['Oscillator0'], data['Oscillator1']
    b['WTOsc1']['relativePathToWT'] = f'{SERUM_TABLES}/not {voice}.wav'
    b['WTOsc1']['numFrames'] = 128 * 2048
    b['plainParams'].update({k: a['plainParams'][k] for k in
                             ('kParamPitchTrack', 'kParamOctave', 'kParamFine')},
                            kParamCoarsePit=a['plainParams']['kParamCoarsePit'] + 12 * math.log2(ratio),
                            kParamEnable=1.0, kParamVolume=0.0)
    a['WTOsc0']['plainParams'].update(kParamWarpMenu='kFM_OSC', kParamWarp=0.0)
    fm_envelope(data, numbers)
    slots = [serum_render.slot(colour, WT_POS_B, 100.0),
             serum_render.slot(ENV3_X_VELO, WARP_A, PEAK_DEPTH)]
    if held:
        hold(kit, data, numbers)
    else:
        # The modulator follows the carrier's strike, so the ratio holds through it.
        strike = data['ModSlot2']['plainParams']['kParamAmount']
        slots.append(serum_render.slot((3, 0), COARSE_B, strike))
    for i, extra in enumerate(slots, start=3):          # the kit uses slots 0-2
        data[f'ModSlot{i}'] = extra
    return data


def baked_data(kit, voice, numbers):
    """The kit's patch on the voice's baked depth table: the same envelope sweeps WT POS."""
    data = kit.patch_data(voice, numbers, percussion.VELO)
    data['Oscillator0']['WTOsc0']['relativePathToWT'] = f'{SERUM_TABLES}/{voice} FM depth.wav'
    fm_envelope(data, numbers)
    data['ModSlot0'] = serum_render.slot(ENV3_X_VELO, WT_POS_A, 100.0)
    return data


def fm_envelope(data, numbers):
    """Envelope 3, the FM depth: no attack, decaying over the voice's median gap."""
    data['Env2']['plainParams'].update(
        kParamAttack=0.0, kParamHold=0.0, kParamDecay=numbers['decay_s'], kParamSustain=0.0)


def hold(kit, data, numbers):
    """Held notes: the strike's pitch slot back to empty, the level sustained."""
    data['ModSlot2'] = copy.deepcopy(kit.init['ModSlot2'])
    data['Env0']['plainParams'].update(kParamDecay=numbers['decay_s'], kParamSustain=1.0,
                                       kParamRelease=numbers['step_s'])


def held_plain_data(kit, voice, numbers):
    data = kit.patch_data(voice, numbers, percussion.NOTE)
    hold(kit, data, numbers)
    return data


# ---------------------------------------------------------------------- the music

def eight_five():
    """eight_five's static set and its voices' numbers, from dois_45's renders of it."""
    folder = DOIS_45 / 'mid' / 'eight_five'
    units = {'A': 120, 'B': 120, 'C': 120, 'D': 192}
    numbers = {}
    for voice, unit in units.items():
        t, onsets = 0, set()
        for msg in mido.MidiFile(folder / f'eight_five_static_{voice}_prime.mid').tracks[0]:
            t += msg.time
            if msg.type == 'note_on' and msg.velocity:
                onsets.add(t // unit)
        layer = [1 if s in onsets else 0 for s in range(40)]
        numbers[voice] = percussion.derive(layer, unit * percussion.SECONDS_PER_TICK)
    return serum_render.tracks(folder / 'eight_five_static_arrangement.mid'), numbers


def held_lattice_midi():
    """dois_45's lattice set with ARTICULATION = 'held', rendered in a scratch copy."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / 'dois_45'
        shutil.copytree(DOIS_45, root, ignore=shutil.ignore_patterns(
            'mid', 'wavetables', 'tuning', '__pycache__', 'tests'))
        config = root / 'config.py'
        config.write_text(config.read_text().replace("ARTICULATION = 'step'", "ARTICULATION = 'held'"))
        # the engine's own Python, which has music21
        subprocess.run(['python3', '-B', 'compose.py'], cwd=root, check=True, capture_output=True)
        return serum_render.tracks(root / 'mid' / 'dois_45_lattice_arrangement.mid')


# ---------------------------------------------------------------------- measuring

WINDOWS = ((0.0, 0.015), (0.015, 0.04), (0.04, 0.08), (0.08, 0.15), (0.15, 0.3))


def centroid(signal, start, seconds=0.08):
    """Spectral centroid in Hz, or None where the stroke has died away (below -60 dB)."""
    seg = signal[int(start * percussion.SR):int((start + seconds) * percussion.SR)]
    if np.sqrt(np.mean(seg ** 2)) < 1e-3 * np.max(np.abs(signal)):
        return None
    mag = np.abs(np.fft.rfft(seg * np.hanning(len(seg))))
    freqs = np.fft.rfftfreq(len(seg), 1 / percussion.SR)
    return round(float((freqs * mag ** 2).sum() / (mag ** 2).sum()))


def write_mp3(name, signal):
    from pedalboard.io import AudioFile
    rms = np.sqrt(np.mean(signal ** 2)) or 1.0
    gain = min(percussion.LOUDNESS / rms, 0.98 / (np.max(np.abs(signal)) or 1.0))
    with AudioFile(str(OUT / name), 'w', percussion.SR, 1, quality=128) as out:
        out.write((signal * gain).astype(np.float32)[None, :])
    print(f"  {name}")


# ------------------------------------------------------------------------ presets

def preset_bytes(data, name, description):
    """A .SerumPreset, marked as a sifters FM pair in its name, author and tags."""
    data = dict(data, fileType='SerumPreset', presetName=name, presetAuthor='sifters',
                presetDescription=description, arpBankDisplayName='', clipBankDisplayName='')
    data.pop('component', None)
    header = {'fileType': 'SerumPreset', 'presetAuthor': 'sifters', 'presetDescription': description,
              'presetName': name, 'product': 'Serum2', 'productVersion': percussion.KNOWN_VERSION[0],
              'tags': ['sifters', 'FM pair', 'Percussion', 'Wavetable'], 'url': 'https://xferrecords.com/',
              'vendor': 'Xfer Records', 'version': percussion.KNOWN_VERSION[1]}
    return serum_state.write_xfer(header, 2, data)


def save_presets(kit, numbers):
    """Every FM pair as a clearly named preset, in its own folder here and in Serum."""
    families = {'A': 'the sieve', 'B': 'its complement', 'C': 'its canon', 'D': 'their intersection'}
    serum = Path(wavetable.serum_presets_folder()) / SERUM_PRESETS
    if PRESETS.exists():
        shutil.rmtree(PRESETS)
    PRESETS.mkdir(parents=True)
    serum.mkdir(parents=True, exist_ok=True)
    patches = {}
    for ratio, value in RATIOS.items():
        for voice in 'ABCD':
            for variant, colour in VARIANTS.items():
                patches[f'sifters FM {voice} {variant} {ratio}'] = (
                    fm_data(kit, voice, numbers[voice], colour, value),
                    f"{variant}: {'velocity' if variant == 'accents' else 'the note'} picks the frame, "
                    f"modulator at {ratio.replace('-', ':')}")
    for voice in 'ABCD':
        patches[f'sifters FM {voice} baked 1-1'] = (baked_data(kit, voice, numbers[voice]), None)
    for name, (data, how) in patches.items():
        voice = name.split()[2]
        decay = f"over {voice}'s median gap ({numbers[voice]['decay_s']:.3f} s)"
        if how is None:
            description = (f"sifters FM, baked. dois_45 voice {voice} ({families[voice]}): a sine "
                           f"phase-modulated by {voice}'s own sieve frame, the depth baked into the "
                           f"table's frames; each stroke starts at velocity's depth and settles into "
                           f"the sine {decay}. Needs Tables/sifters/dois_45 experiments.")
        else:
            description = (f"sifters FM pair. dois_45 voice {voice} ({families[voice]}) on its own "
                           f"sieve table, frequency-modulated by its complement (not {voice}); FM "
                           f"depth decays {decay}, scaled by velocity. {how}. Needs "
                           f"Tables/sifters/dois_44 and dois_45 experiments.")
        (PRESETS / f'{name}.SerumPreset').write_bytes(preset_bytes(data, name, description))
        kit.plugin.raw_state = kit.state(data)
        (PRESETS / f'{name}.vstpreset').write_bytes(kit.plugin.preset_data)
        shutil.copyfile(PRESETS / f'{name}.SerumPreset', serum / f'{name}.SerumPreset')
    print(f"  {len(patches)} presets in {PRESETS} and {serum}")
    return list(patches)


def check_presets(kit, names):
    """Load every .vstpreset back into Serum and confirm the FM pair survived."""
    for name in names:
        kit.plugin.load_preset(str(PRESETS / f'{name}.vstpreset'))
        _, _, _, data = serum_state.read_state(kit.plugin.raw_state)
        voice = name.split()[2]
        a = data['Oscillator0']['WTOsc0']
        if name.endswith('baked 1-1'):
            ok = a['relativePathToWT'].endswith(f'{voice} FM depth.wav')
        else:
            ok = (a['plainParams'].get('kParamWarpMenu') == 'kFM_OSC'
                  and data['Oscillator1']['WTOsc1']['relativePathToWT'].endswith(f'not {voice}.wav'))
        if not ok:
            raise RuntimeError(f"{name}: the FM pair did not survive a round trip through Serum")
    print(f"  all {len(names)} .vstpresets load back into Serum with their FM pair intact")


# ---------------------------------------------------------------------------- run

def main():
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob('*.mp3'):                    # renders only; rebuilt below
        old.unlink()
    deepest = build_tables()
    kit = percussion.Kit()
    numbers = {v: percussion.derive(*r) for v, r in percussion.voice_rhythms().items()}
    mid = percussion.ENGINE / 'mid'
    static, end = serum_render.tracks(mid / 'dois_44_static_arrangement.mid')
    canon, _ = serum_render.tracks(mid / 'dois_44_canon_arrangement.mid')

    def render(name, make, voices, seconds):
        signal = sum(kit.play(kit.state(make(v)), notes, seconds) for v, notes in zip('ABCD', voices))
        write_mp3(name, signal)

    versions = {'kit': lambda v, c: kit.patch_data(v, numbers[v], c),
                'baked': lambda v, c: baked_data(kit, v, numbers[v])}
    versions.update({f'fm_{r}': (lambda value: lambda v, c: fm_data(kit, v, numbers[v], c, value))(x)
                     for r, x in RATIOS.items()})

    # strokes at the eight accent states, and the static set, in every version
    brightness = {}
    for label, make in versions.items():
        brightness[label] = {}
        for voice in 'ABCD':
            notes = [(0.6 * i, numbers[voice]['decay_s'], 36, s) for i, s in enumerate(percussion.STATES)]
            signal = kit.play(kit.state(make(voice, percussion.VELO)), notes, 5.4)
            write_mp3(f'{label}_strokes_{voice}.mp3', signal)
            brightness[label][voice] = {
                'per_state_hz': [centroid(signal, 0.6 * i) for i in range(8)],
                'loudest_over_time_hz': [centroid(signal, 4.2 + a, b - a) for a, b in WINDOWS]}
        render(f'{label}_static.mp3', lambda v: make(v, percussion.VELO), static, end + 1.0)

    # the canon set and held notes, at 1:1
    render('kit_canon.mp3', lambda v: kit.patch_data(v, numbers[v], percussion.NOTE), canon, end + 1.0)
    render('fm_1-1_canon.mp3', lambda v: fm_data(kit, v, numbers[v], percussion.NOTE), canon, end + 1.0)
    held, held_end = held_lattice_midi()
    render('held_lattice.mp3', lambda v: held_plain_data(kit, v, numbers[v]), held, held_end + 1.0)
    render('fm_1-1_held_lattice.mp3', lambda v: fm_data(kit, v, numbers[v], percussion.NOTE, held=True),
           held, held_end + 1.0)

    # eight_five's static set, with its own voices' numbers
    (static85, end85), numbers85 = eight_five()
    render('eight_five_kit_static.mp3', lambda v: kit.patch_data(v, numbers85[v], percussion.VELO),
           static85, end85 + 1.0)
    for ratio, value in RATIOS.items():
        render(f'eight_five_fm_{ratio}_static.mp3',
               lambda v: fm_data(kit, v, numbers85[v], percussion.VELO, value), static85, end85 + 1.0)

    names = save_presets(kit, numbers)
    check_presets(kit, names)
    (HERE / 'fm_summary.json').write_text(json.dumps(
        {'brightness_hz': brightness, 'states': percussion.STATES, 'windows_s': WINDOWS,
         'ratios': RATIOS, 'peak_depth': PEAK_DEPTH / 100, 'baked_depth_rad': deepest,
         'decay_s': {v: round(n['decay_s'], 4) for v, n in numbers.items()},
         'eight_five_D': numbers85['D'], 'presets': names}, indent=1))
    for label in versions:
        print(f"  {label:8s} B's loudest stroke over 0-15-40-80-150-300 ms: "
              f"{brightness[label]['B']['loudest_over_time_hz']}")


if __name__ == '__main__':
    main()
