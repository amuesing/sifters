"""A percussion kit for dois_44, built in Serum 2 from the sieve, and rendered by Serum.

    <python with pedalboard, zstandard, cbor2, mido, numpy> percussion.py [--install]

One rule makes all four patches, as one weather covers all four voices; each voice's own
rhythm supplies the numbers:

  body      the voice's own dois_44 wavetable (its sieve, frame by frame), pitch tracking off
  pitch     the voice's attack rate, raised five octaves: time heard as pitch. A and C strike
            5.4 times a second, so they sound at 172.8 Hz; B 2.6 -> 83.2 Hz; D 3.0 -> 96 Hz
  decay     the voice's median gap between attacks: each stroke rings until the next one
            would come. A and C 0.125 s, B 0.375 s, D 0.333 s
  strike    the pitch falls 390 cents over one step of the voice's grid — the lattice's x13
            in the 40-step tuning, where a step of the sieve is a 5/4 major third
  colour    VELO -> wavetable position: each accent state strikes its own frame
  weight    VELO -> oscillator level, from 0.35 to 1.0, as in the previews

A second set of patches, "lattice", routes NOTE instead of VELO to the wavetable position, so
the canon set's notes, and the form's transpositions, become colours.

Chosen, not derived: the five octaves, the 390 cents' shape (Serum's default curve), the
level range. Everything is written into Serum's own state (serum_state.py); see
serum_render.py for what was measured to make that possible.
"""
import copy
import json
import math
import statistics
import sys
from pathlib import Path

import mido
import numpy as np
import pedalboard
from pedalboard.io import AudioFile

import serum_state

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent / 'dois_44'
sys.path.insert(0, str(ENGINE))
import config                                   # noqa: E402  dois_44's settings: units only
from midi import get_step_ticks                 # noqa: E402

SERUM = '/Library/Audio/Plug-Ins/VST3/Serum2.vst3'
KNOWN_VERSION = ('2.1.5', 11.0)
OUT = HERE / 'audio_kit'
PRESETS = HERE / 'presets'
SR = 44100
LOUDNESS = 0.075
MIDI0_HZ = 8.175798915643707          # where Serum's oscillator sits with pitch tracking off
SECONDS_PER_TICK = 0.5 / config.TICKS_PER_QUARTER_NOTE      # 120 BPM
OCTAVES_UP = 5                        # chosen: brings 2.6-5.4 strokes a second to 83-173 Hz
STRIKE_CENTS = 390                    # the lattice's x13 in the 40-step tuning
SEMITONES_PER_AMOUNT = 1.2            # measured: a pitch mod amount of 10 is ~12 semitones

NOTE, VELO = (17, 0), (16, 0)         # Serum 2's mod-source codes, found by probing
ENV2 = (3, 0)
WT_POS = ('WTOsc', 0, 6, 'kParamTablePos')    # Serum matches by name, but saves 6
OSC_LEVEL = ('Oscillator', 0, 1, 'kParamVolume')
OSC_COARSE = ('Oscillator', 0, 6, 'kParamCoarsePit')
STATES = (1, 19, 37, 55, 73, 91, 109, 127)                  # dois_44's velocity levels


# ----------------------------------------------------------------- what the sieve gives

def voice_rhythms():
    """Each voice's 40-step layer and step length, read from dois_44's own files."""
    out = {}
    for cfg in config.INSTRUMENT_CONFIGS:
        name, unit = cfg['name'], get_step_ticks(cfg)
        t, onsets = 0, set()
        for msg in mido.MidiFile(ENGINE / 'mid' / f'dois_44_static_{name}_prime.mid').tracks[0]:
            t += msg.time
            if msg.type == 'note_on' and msg.velocity:
                onsets.add(t // unit)
        layer = [1 if s in onsets else 0 for s in range(40)]
        out[name] = (layer, unit * SECONDS_PER_TICK)
    return out


def derive(layer, step_seconds):
    attacks = [i for i, on in enumerate(layer) if on]
    gaps = [(b - a) % len(layer) or len(layer) for a, b in zip(attacks, attacks[1:] + attacks[:1])]
    rate = len(attacks) / (len(layer) * step_seconds)
    pitch = rate * 2 ** OCTAVES_UP
    return {'attacks': len(attacks), 'attack_rate_hz': rate, 'pitch_hz': pitch,
            'decay_s': statistics.median(gaps) * step_seconds, 'step_s': step_seconds}


def pitch_controls(hz):
    """OCT, SEM and FINE above MIDI note 0 that reach `hz`."""
    semitones = 12 * math.log2(hz / MIDI0_HZ)
    octave = min(4, int(semitones // 12))
    rest = semitones - 12 * octave
    coarse = int(rest)
    return float(octave), float(coarse), round((rest - coarse) * 100, 2)


# ------------------------------------------------------------------------ the patches

def slot(source, target, amount):
    module, module_id, param_id, name = target
    return {'source': list(source), 'destModuleTypeString': module, 'destModuleID': module_id,
            'destModuleParamID': param_id, 'destModuleParamName': name,
            'plainParams': {'kParamAmount': float(amount)}}


class Kit:
    def __init__(self):
        self.plugin = pedalboard.load_plugin(SERUM, plugin_name='Serum 2')
        self.xml, self.header, self.marker, self.init = serum_state.read_state(self.plugin.raw_state)
        found = (self.header.get('productVersion'), self.init.get('version'))
        if found != KNOWN_VERSION:
            sys.exit(f"Serum reports {found}; this was written against {KNOWN_VERSION}.")

    def patch_data(self, voice, numbers, colour_source):
        data = copy.deepcopy(self.init)
        wt = data['Oscillator0']['WTOsc0']
        wt['relativePathToWT'] = f'sifters/dois_44/{voice}.wav'
        wt['numFrames'] = 128 * 2048
        octave, coarse, fine = pitch_controls(numbers['pitch_hz'])
        data['Oscillator0']['plainParams'].update(
            kParamPitchTrack=0.0, kParamOctave=octave, kParamCoarsePit=coarse, kParamFine=fine,
            kParamVolume=0.35)
        data['Env0']['plainParams'].update(          # Env 1, the amplitude: one stroke
            kParamAttack=0.0, kParamHold=0.0, kParamDecay=numbers['decay_s'],
            kParamSustain=0.0, kParamRelease=numbers['decay_s'])
        data['Env1']['plainParams'].update(          # Env 2, the strike: one step long
            kParamAttack=0.0, kParamHold=0.0, kParamDecay=numbers['step_s'], kParamSustain=0.0)
        data['ModSlot0'] = slot(colour_source, WT_POS, 100.0)
        data['ModSlot1'] = slot(VELO, OSC_LEVEL, 65.0)
        data['ModSlot2'] = slot(ENV2, OSC_COARSE, (STRIKE_CENTS / 100) / SEMITONES_PER_AMOUNT)
        data['Global0']['plainParams'].update(kParamLimitSameNotePolyphony=1.0)
        return data

    def state(self, data):
        return serum_state.write_state(self.xml, self.header, self.marker, data)

    def play(self, state, notes, seconds):
        self.plugin.raw_state = state
        self.plugin.reset()
        messages = []
        for start, length, note, velocity in notes:
            messages.append(mido.Message('note_on', note=note, velocity=velocity, time=start))
            messages.append(mido.Message('note_off', note=note, velocity=0, time=start + length))
        messages.sort(key=lambda m: (m.time, m.type == 'note_on'))
        return self.plugin(messages, duration=seconds, sample_rate=SR).mean(axis=0)


def preset_bytes(data, name, description):
    """A .SerumPreset: the patch, with the fields a saved preset carries."""
    data = dict(data, fileType='SerumPreset', presetName=name, presetAuthor='sifters',
                presetDescription=description, arpBankDisplayName='', clipBankDisplayName='')
    data.pop('component', None)
    header = {'fileType': 'SerumPreset', 'presetAuthor': 'sifters', 'presetDescription': description,
              'presetName': name, 'product': 'Serum2', 'productVersion': KNOWN_VERSION[0],
              'tags': ['Wavetable', 'Percussion', 'sifters'], 'url': 'https://xferrecords.com/',
              'vendor': 'Xfer Records', 'version': KNOWN_VERSION[1]}
    return serum_state.write_xfer(header, 2, data)


# --------------------------------------------------------------------------- rendering

def tracks(path):
    mid = mido.MidiFile(path)
    seconds = 0.5 / mid.ticks_per_beat
    out, end = [], 0
    for track in mid.tracks:
        t, sounding, notes = 0, {}, []
        for msg in track:
            t += msg.time
            if msg.type == 'note_on' and msg.velocity:
                sounding[(msg.channel, msg.note)] = (t, msg.velocity)
            elif msg.type in ('note_off', 'note_on') and (msg.channel, msg.note) in sounding:
                on, velocity = sounding.pop((msg.channel, msg.note))
                notes.append((on * seconds, (t - on) * seconds, msg.note, velocity))
        out.append(notes)
        end = max(end, t * seconds)
    return out, end


def write_mp3(name, signal):
    rms = np.sqrt(np.mean(signal ** 2)) or 1.0
    gain = min(LOUDNESS / rms, 0.98 / (np.max(np.abs(signal)) or 1.0))
    with AudioFile(str(OUT / name), 'w', SR, 1, quality=128) as out:
        out.write((signal * gain).astype(np.float32)[None, :])
    print(f"  {name}")


def main():
    OUT.mkdir(exist_ok=True)
    PRESETS.mkdir(exist_ok=True)
    kit = Kit()
    numbers = {v: derive(*rhythm) for v, rhythm in voice_rhythms().items()}
    patches = {}
    for voice, n in numbers.items():
        for variant, source in (('accents', VELO), ('lattice', NOTE)):
            patches[voice, variant] = kit.patch_data(voice, n, source)

    # the strokes: one hit at each of the eight accent states
    for voice in 'ABCD':
        notes = [(0.6 * i, numbers[voice]['decay_s'], 36, v) for i, v in enumerate(STATES)]
        write_mp3(f'strokes_{voice}.mp3', kit.play(kit.state(patches[voice, 'accents']), notes, 5.4))

    # each voice's line, then the kit, on the static set; the kit on the canon set and form
    static_voices, end = tracks(ENGINE / 'mid' / 'dois_44_static_arrangement.mid')
    mix = 0
    for voice, notes in zip('ABCD', static_voices):
        line = kit.play(kit.state(patches[voice, 'accents']), notes, end + 1.0)
        write_mp3(f'line_{voice}.mp3', line)
        mix = mix + line
    write_mp3('kit_static.mp3', mix)
    for source, name in (('dois_44_canon_arrangement.mid', 'kit_canon.mp3'),
                         ('dois_44_canon_form.mid', 'kit_canon_form.mp3')):
        voices, end = tracks(ENGINE / 'mid' / source)
        mix = 0
        for voice, notes in zip('ABCD', voices):
            mix = mix + kit.play(kit.state(patches[voice, 'lattice']), notes, end + 1.0)
        write_mp3(name, mix)

    # the patches themselves: Serum presets, and VST3 presets as a fallback
    families = {'A': 'the sieve', 'B': 'its complement', 'C': 'its canon', 'D': 'their intersection'}
    for (voice, variant), data in patches.items():
        name = f"sifters {voice} {variant}"
        description = (f"dois_44 voice {voice}, {families[voice]}: its own sieve wavetable at "
                       f"{numbers[voice]['pitch_hz']:.1f} Hz (its attack rate, five octaves up), "
                       f"{numbers[voice]['decay_s']:.3f} s decay (its median gap), a 390-cent strike; "
                       + ("velocity picks the frame." if variant == 'accents' else "note picks the frame."))
        (PRESETS / f"{name}.SerumPreset").write_bytes(preset_bytes(data, name, description))
        kit.plugin.raw_state = kit.state(data)
        (PRESETS / f"{name}.vstpreset").write_bytes(kit.plugin.preset_data)
    (HERE / 'kit_summary.json').write_text(json.dumps(
        {v: {k: round(x, 4) for k, x in n.items()} for v, n in numbers.items()}, indent=1))

    if '--install' in sys.argv:
        install()


def install():
    """The .SerumPreset files into Serum's own presets folder, in a folder labelled with
    the study (User/sifters/dois_44 studies kit), replacing what it held."""
    import shutil
    prefs = Path('~/Library/Preferences/Serum2Prefs.json').expanduser()
    root = Path(json.loads(prefs.read_text())['Serum Presets Path'].rstrip('/'))
    folder = root / 'Presets' / 'User' / 'sifters' / 'dois_44 studies kit'
    folder.mkdir(parents=True, exist_ok=True)
    for old in folder.glob('*.SerumPreset'):
        old.unlink()
    for path in sorted(PRESETS.glob('*.SerumPreset')):
        shutil.copyfile(path, folder / path.name)
    print(f"  presets installed in {folder}")


if __name__ == '__main__':
    main()
