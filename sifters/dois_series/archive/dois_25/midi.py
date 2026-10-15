"""Steps to MIDI, and back again.

Three jobs, in order: work out the meter a period wants (`meter_for`, `shared_meter`),
turn a voice's steps into timed note events (`voice_events`), and write or re-read the
files (`make_track`, `save_tracks`, `read_track`).

`read_track` exists so the checks can read what was actually WRITTEN rather than trust
what was computed.
"""
import glob
import os


import mido
import numpy as np

from config import *


def get_step_ticks(config):
    """Ticks per step. Unknown duration names raise rather than defaulting.

    A silent default here is how the 40/16 meter bug happened in dois_ten: an
    unrecognised value quietly became a sixteenth and nothing downstream could tell.
    """
    if 'step_ticks' in config:
        return config['step_ticks']
    if 'duration' not in config:
        raise KeyError(f"voice {config.get('name')!r} sets neither 'duration' nor "
                       f"'step_ticks'")
    duration = config['duration']
    if duration not in DURATION_MULTIPLIER_KEY:
        raise KeyError(f"voice {config.get('name')!r}: unknown duration {duration!r}. "
                       f"Known: {sorted(DURATION_MULTIPLIER_KEY)}. A triplet or other "
                       f"non-power-of-two grid must set 'step_ticks' directly.")
    return int(TICKS_PER_QUARTER_NOTE * DURATION_MULTIPLIER_KEY[duration])

def meter_for(bar_ticks, denominators=(16, 8, 4, 32, 2, 64, 1)):
    """A meter whose bar is exactly `bar_ticks`, or None."""
    for den in denominators:
        beat_ticks = (4 * TICKS_PER_QUARTER_NOTE) / den
        if beat_ticks != int(beat_ticks):
            continue
        beat_ticks = int(beat_ticks)
        if bar_ticks % beat_ticks == 0:
            numerator = bar_ticks // beat_ticks
            if 1 <= numerator <= MAX_METER_NUMERATOR:
                return numerator, den
    return None

def meter_for_voice(step_ticks, note_layer_ticks, period_ticks):
    """A meter in which this voice's clip ends exactly on a bar line.

    Preference 1 — the beat IS the voice's basic unit and the bar is one pass of the
    note layer. A sixteenth grid gives 4*TPQ/120 = 16, so 40 steps is 40/16.

    Preference 2 — a grid that is not a power-of-two subdivision cannot be a beat
    (a triplet gives 4*TPQ/160 = 12, not a valid denominator). Fall back to any meter
    whose BAR equals the voice's whole period: the beat is then not the voice's unit,
    but the bar still lands on the period, which is what stops a host padding the clip.
    """
    denominator = (4 * TICKS_PER_QUARTER_NOTE) / step_ticks
    if denominator == int(denominator) and not (int(denominator) & (int(denominator) - 1)):
        numerator = note_layer_ticks // step_ticks
        if 1 <= numerator <= MAX_METER_NUMERATOR:
            return int(numerator), int(denominator)
    return meter_for(period_ticks, denominators=(4, 8, 16, 2, 32, 1, 64))

def shared_meter(lengths, candidate_bars):
    """One meter for every voice, when one exists.

    A candidate bar is one pass of SOME voice's note layer at that voice's own basic
    unit. Voices may have different note layers and different units, so each offers a
    different candidate. One can be shared only if it divides EVERY length — otherwise
    a clip would not end on a bar line and the host would pad it — and is expressible
    as a meter at all. The finest workable bar wins, so the beat stays a real
    subdivision rather than a coarse container.
    """
    for bar in sorted(set(candidate_bars)):
        if any(length % bar for length in lengths):
            continue
        meter = meter_for(bar)
        if meter:
            return meter
    return None


def append_header(track, name, meter, provenance=None):
    track.append(mido.MetaMessage('track_name', name=name, time=0))
    if provenance:
        track.append(mido.MetaMessage('text', text=provenance, time=0))
    numerator, denominator = meter
    track.append(mido.MetaMessage('time_signature', numerator=numerator,
                                  denominator=denominator, time=0))
    track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(TEMPO_BPM), time=0))


#
# Ensemble files repeat each voice a WHOLE number of its own periods, enough for every
# voice to finish together. A period is never stretched or truncated to fit, so one
# cycle inside an ensemble file equals that voice's own file exactly — which is what
# makes the per-voice files usable to check the ensemble.

def gate_ticks(step_ticks):
    """How long a note sounds, from GATE_RATIO.

    A ratio of 1.0 fills the step, so consecutive notes abut — legal MIDI, and what
    lets a complement pair tile time continuously. Anything below leaves a gap, which
    is what a device needs if it will not retrigger from a zero-length one.
    """
    return max(1, min(int(round(step_ticks * GATE_RATIO)), step_ticks))

def voice_events(notes_per_step, velocities, step_ticks, total_ticks, channel=0):
    """Absolute-time (tick, kind, pitch, velocity, channel); kind 1 = on, 0 = off."""
    active = np.flatnonzero(velocities)
    if active.size == 0:
        return []
    cycle_ticks = len(velocities) * step_ticks
    if total_ticks % cycle_ticks:
        raise ValueError(f"{total_ticks} is not a whole number of {cycle_ticks}-tick "
                         f"cycles; a voice would be cut mid-period")
    events = []
    for rep in range(total_ticks // cycle_ticks):
        rep_start = rep * cycle_ticks
        for idx in active:
            on_tick = rep_start + int(idx) * step_ticks
            velocity = int(velocities[idx])
            for pitch in notes_per_step[idx]:
                events.append((on_tick,                       1, int(pitch), velocity, channel))
                events.append((on_tick + gate_ticks(step_ticks), 0, int(pitch), 0, channel))
    return events

def make_track(name, events, total_ticks, meter, provenance=None):
    track = mido.MidiTrack()
    append_header(track, name, meter, provenance)

    # note_off (kind 0) sorts ahead of note_on at the same tick, so a pitch that
    # retriggers on consecutive steps releases before it strikes again.
    prev = 0
    for abs_tick, kind, pitch, vel, chan in sorted(events, key=lambda e: (e[0], e[1])):
        track.append(mido.Message('note_on' if kind == 1 else 'note_off', channel=chan,
                                  note=pitch, velocity=vel, time=abs_tick - prev))
        prev = abs_tick

    if prev > total_ticks:
        raise ValueError(f"track {name!r} has events past its {total_ticks}-tick end")
    # Pad to the true boundary so the host reads the correct clip length rather than
    # stopping at the last note.
    track.append(mido.MetaMessage('end_of_track', time=total_ticks - prev))
    return track

def save_tracks(tracks, filename, total_ticks, meter, note=''):
    if not tracks:
        print(f"  Skipped {filename}: no tracks")
        return
    mid = mido.MidiFile(ticks_per_beat=TICKS_PER_QUARTER_NOTE)
    mid.tracks.extend(tracks)

    numerator, denominator = meter
    bar_ticks = numerator * (4 * TICKS_PER_QUARTER_NOTE) // denominator
    warning = "" if total_ticks % bar_ticks == 0 else "  <-- NOT whole bars, host will pad"
    try:
        mid.save(os.path.join(OUTPUT_DIR, f"{filename}.mid"))
        print(f"  Saved: {filename}.mid  ({total_ticks} ticks = "
              f"{total_ticks / bar_ticks:g} bars of {numerator}/{denominator}{note})"
              f"{warning}")
    except OSError as e:
        raise RuntimeError(f"could not save {filename}: {e}") from e


def read_track(path, track_index=None, pitch=None, channel=None):
    """(onset, duration, pitch, velocity) for a file, one track, pitch or channel.

    Sounding notes are keyed by (channel, pitch), not pitch alone: in the merged file
    each voice has its own channel, and keying by pitch alone would confuse two voices
    that share one. (It also allowed the derived-pitch versions to sound unisons.)
    """
    notes, hanging, overlaps = [], [], []
    midi = mido.MidiFile(path)
    for i, track in enumerate(midi.tracks):
        if track_index is not None and i != track_index:
            continue
        t, open_notes = 0, {}
        for msg in track:
            t += msg.time
            key = (msg.channel, msg.note) if msg.type in ('note_on', 'note_off') else None
            if msg.type == 'note_on' and msg.velocity > 0:
                if key in open_notes:
                    overlaps.append((msg.note, t))
                open_notes[key] = (t, msg.velocity)
            elif msg.type in ('note_off', 'note_on') and key in open_notes:
                onset, vel = open_notes.pop(key)
                if ((pitch is None or msg.note == pitch)
                        and (channel is None or msg.channel == channel)):
                    notes.append((onset, t - onset, msg.note, vel))
        hanging.extend(open_notes)
    return sorted(notes), hanging, overlaps

def track_meta(path):
    """[(name, (num, den), tempo, end_tick)] per track."""
    out = []
    for track in mido.MidiFile(path).tracks:
        t, name, sig, tempo = 0, None, None, None
        for msg in track:
            t += msg.time
            if msg.type == 'track_name':
                name = msg.name
            elif msg.type == 'time_signature':
                sig = (msg.numerator, msg.denominator)
            elif msg.type == 'set_tempo':
                tempo = msg.tempo
        out.append((name, sig, tempo, t))
    return out

def rhythm_from_file(path, step_ticks, note_layer_steps):
    """Read a voice's note layer back out of its rendered file.

    Returns the note layer, and whether the file is genuinely periodic on it — if the
    rendered onsets do not repeat every `note_layer_steps`, the file is not a tiling of
    the sieve at all and the derivation check below would be meaningless.
    """
    notes, _, _ = read_track(path)
    total = max(o + d for o, d, _, _ in notes)
    grid = np.zeros(-(-total // step_ticks), dtype=int)
    for onset, _, _, _ in notes:
        grid[onset // step_ticks] = 1
    layer = grid[:note_layer_steps]
    periodic = all(grid[i] == layer[i % note_layer_steps] for i in range(len(grid)))
    return layer, periodic


def clear_our_outputs(filenames):
    """Remove only the files this run will write.

    dois_eleven emptied the whole output directory, which destroyed anything saved or
    edited there. Only our own filenames are replaced; everything else is left alone
    and reported.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    ours = {f"{name}.mid" for name in filenames}
    for path in glob.glob(os.path.join(OUTPUT_DIR, '*.mid')):
        if os.path.basename(path) in ours:
            os.remove(path)
    kept = sorted(os.path.basename(p) for p in glob.glob(os.path.join(OUTPUT_DIR, '*.mid')))
    if kept:
        print(f"  leaving {len(kept)} other file(s) in mid/ untouched: {', '.join(kept)}")
