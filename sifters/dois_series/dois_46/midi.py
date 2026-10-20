"""Steps to MIDI, and back again."""
import contextlib
import os
import shutil
import tempfile

import mido
import numpy as np

import config


# ------------------------------------------------------------------ where files go
#
# Each kind of file has its own folder (config.OUTPUT_DIRS), chosen by its extension.
# Renders go to a STAGING folder first and only move into those folders once every pitch
# mode has been written AND verified, so a failed or interrupted run moves nothing.
KINDS = {'.mid': 'mid', '.wav': 'wavetables', '.txt': 'wavetables',
         '.tun': 'tuning', '.scl': 'tuning', '.kbm': 'tuning', '.SerumPreset': 'presets'}
_staging = None


def kind_of(filename):
    """'mid', 'wavetables', 'tuning' or 'presets'. A name without an extension is MIDI."""
    return KINDS[os.path.splitext(filename)[1] or '.mid']


def output_dir(kind='mid'):
    """Where files of this kind are being written or read right now."""
    return os.path.join(_staging, kind) if _staging else config.OUTPUT_DIRS[kind]


@contextlib.contextmanager
def staged_output():
    """Render into a staging folder beside the output folders, one subfolder per kind
    (same filesystem, so committing is a rename). Leaving without `commit_staged`
    throws the staged files away."""
    global _staging
    home = os.path.dirname(config.OUTPUT_DIRS['mid'])
    os.makedirs(home, exist_ok=True)
    _staging = tempfile.mkdtemp(prefix='.staging-', dir=home)
    for kind in config.OUTPUT_DIRS:
        os.makedirs(os.path.join(_staging, kind))
    try:
        yield
    finally:
        staged, _staging = _staging, None
        shutil.rmtree(staged, ignore_errors=True)


def commit_staged(filenames):
    """Move the verified renders into their folders, replacing only our own files.

    `os.replace` is atomic per file, and every byte was written and verified before the
    first one moves.
    """
    if _staging is None:
        raise RuntimeError('commit_staged() outside staged_output()')
    ours = {name if os.path.splitext(name)[1] else f"{name}.mid" for name in filenames}
    moved = dict.fromkeys(config.OUTPUT_DIRS, 0)
    for name in sorted(ours):
        kind = kind_of(name)
        staged = os.path.join(_staging, kind, name)
        final = os.path.join(config.OUTPUT_DIRS[kind], name)
        if os.path.exists(staged):
            os.makedirs(config.OUTPUT_DIRS[kind], exist_ok=True)
            os.replace(staged, final)
            moved[kind] += 1
        elif os.path.exists(final):
            os.remove(final)          # we own the name but did not produce it this run
    kept = sorted(entry.name for folder in config.OUTPUT_DIRS.values() if os.path.isdir(folder)
                  for entry in os.scandir(folder)
                  if entry.is_file() and not entry.name.startswith('.')
                  and entry.name not in ours)
    print(f"\n  {sum(moved.values())} file(s) moved into place after every mode verified: "
          + ", ".join(f"{n} into {kind}/" for kind, n in moved.items() if n))
    if kept:
        print(f"  leaving {len(kept)} other file(s) there untouched: {', '.join(kept)}")


# ------------------------------------------------------------------- timing and meter

def get_step_ticks(cfg):
    """Ticks per step. An unknown duration name raises rather than defaulting."""
    if 'step_ticks' in cfg:
        return cfg['step_ticks']
    if 'duration' not in cfg:
        raise KeyError(f"voice {cfg.get('name')!r} sets neither 'duration' nor "
                       f"'step_ticks'")
    duration = cfg['duration']
    if duration not in config.DURATION_MULTIPLIER_KEY:
        raise KeyError(f"voice {cfg.get('name')!r}: unknown duration {duration!r}. "
                       f"Known: {sorted(config.DURATION_MULTIPLIER_KEY)}. A triplet or other "
                       f"non-power-of-two grid must set 'step_ticks' directly.")
    return int(config.TICKS_PER_QUARTER_NOTE * config.DURATION_MULTIPLIER_KEY[duration])


def meter_for(bar_ticks, denominators=(16, 8, 4, 32, 2, 64, 1)):
    """A meter whose bar is exactly `bar_ticks`, or None."""
    for den in denominators:
        beat_ticks = (4 * config.TICKS_PER_QUARTER_NOTE) / den
        if beat_ticks != int(beat_ticks):
            continue
        beat_ticks = int(beat_ticks)
        if bar_ticks % beat_ticks == 0:
            numerator = bar_ticks // beat_ticks
            if 1 <= numerator <= config.MAX_METER_NUMERATOR:
                return numerator, den
    return None


def meter_for_voice(step_ticks, note_layer_ticks, period_ticks):
    """A meter in which this voice's clip ends exactly on a bar line."""
    denominator = (4 * config.TICKS_PER_QUARTER_NOTE) / step_ticks
    if denominator == int(denominator) and not (int(denominator) & (int(denominator) - 1)):
        numerator = note_layer_ticks // step_ticks
        if 1 <= numerator <= config.MAX_METER_NUMERATOR:
            return int(numerator), int(denominator)
    return meter_for(period_ticks, denominators=(4, 8, 16, 2, 32, 1, 64))


def shared_meter(lengths, candidate_bars):
    """One meter for every voice, when one exists."""
    for bar in sorted(set(candidate_bars)):
        if any(length % bar for length in lengths):
            continue
        meter = meter_for(bar)
        if meter:
            return meter
    return None


# ------------------------------------------------------------------- writing MIDI

def append_header(track, name, meter, provenance=None):
    track.append(mido.MetaMessage('track_name', name=name, time=0))
    if provenance:
        track.append(mido.MetaMessage('text', text=provenance, time=0))
    numerator, denominator = meter
    track.append(mido.MetaMessage('time_signature', numerator=numerator,
                                  denominator=denominator, time=0))
    track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(config.TEMPO_BPM), time=0))


def gate_ticks(step_ticks):
    """How long a 'step' note sounds: GATE_RATIO of the step (1.0 fills it, so notes
    abut; below 1.0 leaves the gap a device that will not retrigger needs)."""
    return max(1, min(int(round(step_ticks * config.GATE_RATIO)), step_ticks))


def note_lengths(velocities, step_ticks):
    """How long each sounding step's note lasts, in ticks, keyed by step.

    'step' fills the step at GATE_RATIO. 'held' holds every note until the voice's next
    attack (the last until the end of its statement), so the sieve's gaps become
    durations and a synth's envelopes and wavetable position have time to move.
    """
    active = [int(i) for i in np.flatnonzero(velocities)]
    if config.ARTICULATION == 'held':
        ends = active[1:] + [len(velocities)]
        return {i: (end - i) * step_ticks for i, end in zip(active, ends)}
    if config.ARTICULATION != 'step':
        raise ValueError(f"ARTICULATION must be 'step' or 'held', not "
                         f"{config.ARTICULATION!r}")
    return {i: gate_ticks(step_ticks) for i in active}


def voice_events(notes_per_step, velocities, step_ticks, total_ticks, channel=0):
    """Absolute-time (tick, kind, pitch, velocity, channel); kind 1 = on, 0 = off.

    A voice repeats a WHOLE number of its own periods, never stretched or cut, so one
    cycle inside an ensemble file equals that voice's own file exactly.
    """
    active = np.flatnonzero(velocities)
    if active.size == 0:
        return []
    cycle_ticks = len(velocities) * step_ticks
    if total_ticks % cycle_ticks:
        raise ValueError(f"{total_ticks} is not a whole number of {cycle_ticks}-tick "
                         f"cycles; a voice would be cut mid-period")
    lengths = note_lengths(velocities, step_ticks)
    events = []
    for rep in range(total_ticks // cycle_ticks):
        rep_start = rep * cycle_ticks
        for idx in active:
            on_tick = rep_start + int(idx) * step_ticks
            velocity = int(velocities[idx])
            for pitch in notes_per_step[idx]:
                events.append((on_tick,                       1, int(pitch), velocity, channel))
                events.append((on_tick + lengths[int(idx)], 0, int(pitch), 0, channel))
    return events


def make_track(name, events, total_ticks, meter, provenance=None):
    track = mido.MidiTrack()
    append_header(track, name, meter, provenance)
    # note_off sorts ahead of note_on at the same tick, so a retriggered pitch releases
    # before it strikes again.
    prev = 0
    for abs_tick, kind, pitch, vel, chan in sorted(events, key=lambda e: (e[0], e[1])):
        track.append(mido.Message('note_on' if kind == 1 else 'note_off', channel=chan,
                                  note=pitch, velocity=vel, time=abs_tick - prev))
        prev = abs_tick
    if prev > total_ticks:
        raise ValueError(f"track {name!r} has events past its {total_ticks}-tick end")
    # Padded to the true boundary, so a host reads the clip's real length.
    track.append(mido.MetaMessage('end_of_track', time=total_ticks - prev))
    return track


def save_tracks(tracks, filename, total_ticks, meter, note=''):
    if not tracks:
        print(f"  Skipped {filename}: no tracks")
        return
    mid = mido.MidiFile(ticks_per_beat=config.TICKS_PER_QUARTER_NOTE)
    mid.tracks.extend(tracks)
    numerator, denominator = meter
    bar_ticks = numerator * (4 * config.TICKS_PER_QUARTER_NOTE) // denominator
    warning = "" if total_ticks % bar_ticks == 0 else "  <-- NOT whole bars, host will pad"
    try:
        mid.save(os.path.join(output_dir(), f"{filename}.mid"))
        print(f"  Saved: {filename}.mid  ({total_ticks} ticks = "
              f"{total_ticks / bar_ticks:g} bars of {numerator}/{denominator}{note})"
              f"{warning}")
    except OSError as e:
        raise RuntimeError(f"could not save {filename}: {e}") from e


# ------------------------------------------------------------------- reading MIDI back

def read_track(path, track_index=None, pitch=None, channel=None):
    """(notes, hanging, overlaps) for a file, one track, pitch or channel; each note is
    (onset, duration, pitch, velocity). Sounding notes are keyed by (channel, pitch),
    so two voices sharing a pitch in the merged file are never confused."""
    notes, hanging, overlaps = [], [], []
    for i, track in enumerate(mido.MidiFile(path).tracks):
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
    """A voice's note layer read back from its file, and whether the file is genuinely
    periodic on it. The length is where the track ENDS, not where its last note stops,
    so a single pass ending on a rest keeps its last step."""
    notes, _, _ = read_track(path)
    track_end = max(sum(msg.time for msg in track) for track in mido.MidiFile(path).tracks)
    total = max(track_end, max(o + d for o, d, _, _ in notes))
    grid = np.zeros(-(-total // step_ticks), dtype=int)
    for onset, _, _, _ in notes:
        grid[onset // step_ticks] = 1
    layer = grid[:note_layer_steps]
    periodic = all(grid[i] == layer[i % note_layer_steps] for i in range(len(grid)))
    return layer, periodic
