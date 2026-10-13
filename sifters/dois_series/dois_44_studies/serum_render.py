"""Render the studies through Serum 2 itself — the same MIDI as the Python previews.

    <python with pedalboard, zstandard, cbor2, mido, numpy> serum_render.py

Serum 2 is loaded with Spotify's pedalboard, which hosts VST3 instruments in Python and
plays MIDI through them offline. No DAW and no Serum window: each patch is written in code,
by editing Serum's own saved state (serum_state.py). Every patch starts from Serum's init
patch and changes only:

  * oscillator A's wavetable — a sifters table from Serum's Tables folder;
  * pitch tracking OFF, with OCT and SEM setting a fixed pitch per voice;
  * one routing: NOTE or VELO -> oscillator A's wavetable position, 100%;
  * for the NOTE studies, a second routing, VELO -> oscillator A's level, so velocity is
    heard as loudness as in the Python previews.

The pitched studies (4 and 5) use the init patch untouched, pitch tracking on, at the
pitches the MIDI writes. Their 40-step versions are not rendered: how Serum stores a tuning
file in its state was not found, so those stay as Python previews.

Measured while building this (Serum 2.1.5): with pitch tracking off the oscillator plays
MIDI note 0, 8.18 Hz, and OCT/SEM move it from there — OCT +4 is 130.8 Hz. NOTE is mod
source 17 and VELO is 16, and at 100% both put value v exactly on frame v of a 128-frame
table, as dois_41's README assumed.

Unofficial: Serum's state format is undocumented, so this refuses any version other than
the one it was read from.
"""
import copy
import struct
import sys
from pathlib import Path

import mido
import numpy as np
import pedalboard

import serum_state

HERE = Path(__file__).resolve().parent
ENGINE_MID = HERE.parent / 'dois_44' / 'mid'
OUT = HERE / 'audio_serum'
SERUM = '/Library/Audio/Plug-Ins/VST3/Serum2.vst3'
KNOWN_VERSION = ('2.1.5', 11.0)       # productVersion, state version this was read from
SR = 44100
LOUDNESS = 0.075                      # the previews' RMS, so the two sets compare fairly

NOTE, VELO = (17, 0), (16, 0)         # Serum 2's mod-source codes, found by probing
WT_POS = ('WTOsc', 0, 1, 'kParamTablePos')
OSC_LEVEL = ('Oscillator', 0, 1, 'kParamVolume')
# Above MIDI note 0 (8.18 Hz): A 110 Hz, B 165 Hz, C 131 Hz, D 82 Hz, as in the previews.
FIXED = {'A': (3, 9), 'B': (4, 4), 'C': (4, 0), 'D': (3, 4)}


def slot(source, target, amount):
    module, module_id, param_id, name = target
    return {'source': list(source), 'destModuleTypeString': module, 'destModuleID': module_id,
            'destModuleParamID': param_id, 'destModuleParamName': name,
            'plainParams': {'kParamAmount': float(amount)}}


class Serum:
    def __init__(self):
        self.plugin = pedalboard.load_plugin(SERUM, plugin_name='Serum 2')
        self.xml, self.header, self.marker, self.init = serum_state.read_state(
            self.plugin.raw_state)
        found = (self.header.get('productVersion'), self.init.get('version'))
        if found != KNOWN_VERSION:
            sys.exit(f"Serum reports {found}; this was written against {KNOWN_VERSION}. Its "
                     f"state format is undocumented, so nothing was rendered.")

    def wavetable_patch(self, table, voice, source):
        data = copy.deepcopy(self.init)
        wt = data['Oscillator0']['WTOsc0']
        wt['relativePathToWT'] = table
        wt['numFrames'] = 128 * 2048
        octave, semitone = FIXED[voice]
        params = data['Oscillator0']['plainParams']
        params.update(kParamPitchTrack=0.0, kParamOctave=float(octave),
                      kParamCoarsePit=float(semitone))
        data['ModSlot0'] = slot(source, WT_POS, 100.0)
        if source == NOTE:
            params['kParamVolume'] = 0.35
            data['ModSlot1'] = slot(VELO, OSC_LEVEL, 65.0)
        return serum_state.write_state(self.xml, self.header, self.marker, data)

    def init_patch(self):
        return serum_state.write_state(self.xml, self.header, self.marker, self.init)

    def play(self, state, notes, seconds):
        self.plugin.raw_state = state
        self.plugin.reset()
        messages = []
        for start, length, note, velocity in notes:
            messages.append(mido.Message('note_on', note=note, velocity=velocity, time=start))
            messages.append(mido.Message('note_off', note=note, velocity=0, time=start + length))
        messages.sort(key=lambda m: (m.time, m.type == 'note_on'))
        return self.plugin(messages, duration=seconds, sample_rate=SR).mean(axis=0)


def tracks(path):
    """[[(start s, length s, note, velocity)] per track], and the file's length in seconds."""
    mid = mido.MidiFile(path)
    seconds_per_tick = 0.5 / mid.ticks_per_beat           # 120 BPM, as the piece states
    out, end = [], 0
    for track in mid.tracks:
        t, sounding, notes = 0, {}, []
        for msg in track:
            t += msg.time
            if msg.type == 'note_on' and msg.velocity:
                sounding[(msg.channel, msg.note)] = (t, msg.velocity)
            elif msg.type in ('note_off', 'note_on') and (msg.channel, msg.note) in sounding:
                on, velocity = sounding.pop((msg.channel, msg.note))
                notes.append((on * seconds_per_tick, (t - on) * seconds_per_tick, msg.note, velocity))
        out.append(notes)
        end = max(end, t * seconds_per_tick)
    return out, end


def write_wav(path, signal):
    rms = np.sqrt(np.mean(signal ** 2)) or 1.0
    gain = min(LOUDNESS / rms, 0.98 / (np.max(np.abs(signal)) or 1.0))
    data = (np.clip(signal * gain, -1, 1) * 32767).astype('<i2').tobytes()
    header = (b'RIFF' + struct.pack('<I', 36 + len(data)) + b'WAVE'
              + b'fmt ' + struct.pack('<IHHIIHH', 16, 1, 1, SR, SR * 2, 2, 16)
              + b'data' + struct.pack('<I', len(data)))
    path.write_bytes(header + data)


def render_wavetables(serum, midi, tables, source, name):
    voices, end = tracks(midi)
    mix = 0
    for voice, notes in zip('ABCD', voices):
        if notes:
            mix = mix + serum.play(serum.wavetable_patch(tables[voice], voice, source), notes, end + 1.0)
    write_wav(OUT / name, mix)
    print(f"  {name}")


def render_pitched(serum, midi, name):
    voices, end = tracks(midi)
    mix = 0
    for notes in voices:                 # one track at a time: no voice is ever stolen
        if notes:
            mix = mix + serum.play(serum.init_patch(), notes, end + 1.5)
    write_wav(OUT / name, mix)
    print(f"  {name}")


def main():
    OUT.mkdir(exist_ok=True)
    serum = Serum()
    own = {v: f'sifters/dois_44/{v}.wav' for v in 'ABCD'}
    grid = {v: 'sifters/dois_44 experiments/fm grid.wav' for v in 'ABCD'}
    pm = {v: f'sifters/dois_44 experiments/pm sieve {v}.wav' for v in 'ABCD'}
    static, lattice = ENGINE_MID / 'dois_44_static_arrangement.mid', ENGINE_MID / 'dois_44_lattice_arrangement.mid'
    study = HERE / 'mid'

    render_wavetables(serum, static, own, VELO, '1a_dois44_velocity_8_states.wav')
    render_wavetables(serum, study / 'study1_second_accent_static_arrangement.mid', own, VELO,
                      '1b_second_accent_velocity_16_states.wav')
    render_wavetables(serum, static, own, NOTE, '2a_dois44_one_timbre_per_voice.wav')
    render_wavetables(serum, study / 'study2_clauses_arrangement.mid', own, NOTE,
                      '2b_clauses_a_timbre_per_clause.wav')
    render_wavetables(serum, lattice, own, NOTE, '3a_dois44_additive_table.wav')
    render_wavetables(serum, lattice, grid, NOTE, '3b_fm_grid_table.wav')
    render_wavetables(serum, lattice, pm, NOTE, '3c_pm_by_sieve_table.wav')
    render_pitched(serum, study / 'study4_prolation_lattice_arrangement.mid', '4_prolation_canon.wav')
    render_pitched(serum, lattice, '5a_dois44_lattice_12tet.wav')
    render_pitched(serum, ENGINE_MID / 'dois_44_canon_arrangement.mid', '5b_dois44_canon_12tet.wav')
    render_pitched(serum, study / 'study5_multipliers_arrangement.mid', '5c_four_multipliers_12tet.wav')


if __name__ == '__main__':
    main()
