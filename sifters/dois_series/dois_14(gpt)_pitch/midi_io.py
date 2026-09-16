"""Strict MIDI readback and publication of complete, verified render generations."""
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import tempfile

import mido
from .engine import ENGINE_VERSION, Note, canonical, validate_grid


def expected_files(plan):
    result = {f'{plan.title}_{v.name}_prime.mid': ((v.name, v.notes),) for v in plan.voices}
    result[f'{plan.title}_arrangement.mid'] = tuple((v.name, v.notes) for v in plan.voices)
    result[f'{plan.title}_ensemble.mid'] = ((f'{plan.title} pitched ensemble', tuple(sorted(
        note for v in plan.voices for note in v.notes))),)
    return result


def provenance(plan, name):
    return f'{plan.title} engine={ENGINE_VERSION} cfg={plan.fingerprint} parity={plan.parity} track={name}'


def write_files(plan, directory):
    for filename, expected_tracks in expected_files(plan).items():
        midi = mido.MidiFile(type=1, ticks_per_beat=plan.tpq)
        for name, notes in expected_tracks:
            track = mido.MidiTrack()
            track.extend([
                mido.MetaMessage('track_name', name=name),
                mido.MetaMessage('text', text=provenance(plan, name)),
                mido.MetaMessage('time_signature', numerator=plan.meter[0], denominator=plan.meter[1]),
                mido.MetaMessage('set_tempo', tempo=plan.tempo),
            ])
            events = sorted([(n.onset, 1, n.channel, n.pitch, n.velocity) for n in notes] +
                            [(n.onset + n.duration, 0, n.channel, n.pitch, 0) for n in notes])
            previous = 0
            for tick, kind, channel, pitch, velocity in events:
                track.append(mido.Message('note_on' if kind else 'note_off', channel=channel,
                                          note=pitch, velocity=velocity, time=tick - previous))
                previous = tick
            track.append(mido.MetaMessage('end_of_track', time=plan.parity - previous))
            midi.tracks.append(track)
        path = directory / filename
        # A copied old file could be a symlink; never follow it while overwriting.
        if path.is_symlink():
            path.unlink()
        midi.save(path)


def read_track(track, plan, expected_name):
    tick, active, notes, metadata = 0, {}, [], {}
    for i, msg in enumerate(track):
        if type(msg.time) is not int or msg.time < 0:
            raise ValueError(f'{expected_name}: invalid delta time')
        tick += msg.time
        if tick > plan.parity:
            raise ValueError(f'{expected_name}: event past first parity')
        if msg.is_meta:
            if msg.type == 'end_of_track':
                if i != len(track) - 1 or tick != plan.parity:
                    raise ValueError(f'{expected_name}: incorrect end-of-track boundary')
            elif msg.type in ('track_name', 'text', 'time_signature', 'set_tempo'):
                if tick != 0:
                    raise ValueError(f'{expected_name}: metadata changes inside the clip')
            else:
                raise ValueError(f'{expected_name}: unexpected metadata {msg.type}')
            metadata.setdefault(msg.type, []).append(msg)
            continue
        if msg.type not in ('note_on', 'note_off'):
            raise ValueError(f'{expected_name}: unexpected MIDI message {msg.type}')
        key = msg.channel, msg.note
        if msg.type == 'note_on' and msg.velocity > 0:
            if key in active:
                raise ValueError(f'{expected_name}: overlapping note {key}')
            active[key] = tick, msg.velocity
        else:
            if key not in active:
                raise ValueError(f'{expected_name}: orphan note-off {key}')
            onset, velocity = active.pop(key)
            if tick <= onset:
                raise ValueError(f'{expected_name}: nonpositive note duration')
            notes.append(Note(onset, tick - onset, msg.channel, msg.note, velocity))
    if active:
        raise ValueError(f'{expected_name}: hanging notes {list(active)}')
    types = ('track_name', 'text', 'time_signature', 'set_tempo', 'end_of_track')
    if set(metadata) != set(types) or any(len(metadata[t]) != 1 for t in types):
        raise ValueError(f'{expected_name}: missing or duplicate metadata')
    signature = metadata['time_signature'][0]
    if (signature.numerator, signature.denominator) != plan.meter or signature.clocks_per_click != 24 or signature.notated_32nd_notes_per_beat != 8:
        raise ValueError(f'{expected_name}: unexpected time signature')
    if metadata['track_name'][0].name != expected_name:
        raise ValueError(f'{expected_name}: unexpected track name')
    if metadata['text'][0].text != provenance(plan, expected_name):
        raise ValueError(f'{expected_name}: incorrect provenance')
    if metadata['set_tempo'][0].tempo != plan.tempo:
        raise ValueError(f'{expected_name}: unexpected tempo')
    return tuple(sorted(notes))


def verify_files(plan, directory):
    """Check every event and every voice grid in all six output representations."""
    directory = Path(directory).resolve()
    for filename, expected_tracks in expected_files(plan).items():
        try:
            midi = mido.MidiFile(directory / filename)
        except (OSError, EOFError, ValueError) as exc:
            raise ValueError(f'{filename}: could not read MIDI: {exc}') from exc
        if midi.type != 1 or midi.ticks_per_beat != plan.tpq:
            raise ValueError(f'{filename}: incorrect MIDI type or PPQ')
        if len(midi.tracks) != len(expected_tracks):
            raise ValueError(f'{filename}: incorrect track inventory')
        for track, (name, expected) in zip(midi.tracks, expected_tracks):
            actual = read_track(track, plan, name)
            if actual != tuple(sorted(expected)):
                raise ValueError(f'{filename}/{name}: rendered notes differ from the expected composition')
            relevant = plan.voices if name == f'{plan.title} pitched ensemble' else tuple(v for v in plan.voices if v.name == name)
            for voice in relevant:
                grid = [0] * (plan.parity // voice.unit)
                for note in actual:
                    if note.channel != voice.channel:
                        continue
                    if note.onset % voice.unit:
                        raise ValueError(f'{filename}/{voice.name}: off-grid note')
                    index = note.onset // voice.unit
                    if index >= len(grid) or grid[index]:
                        raise ValueError(f'{filename}/{voice.name}: extra onset')
                    grid[index] = note.velocity
                validate_grid(grid, voice.layer, f'{filename}/{voice.name}')
                if tuple(grid) != voice.velocities:
                    raise ValueError(f'{filename}/{voice.name}: wrong rendered accent field')
    return True


def manifest(plan, directory):
    return {
        'engine_version': ENGINE_VERSION,
        'configuration': json.loads(plan.configuration_json),
        'configuration_sha256': plan.fingerprint,
        'parity_ticks': plan.parity,
        'meter': plan.meter,
        'rendered_at_utc': datetime.now(timezone.utc).isoformat(),
        'dependencies': {name: version(name) for name in ('mido', 'music21', 'numpy')},
        'engine_source_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in sorted(Path(__file__).parent.glob('*.py'))},
        'voices': [{
            'name': v.name, 'pitch_root': v.pitch, 'channel': v.channel + 1, 'step_ticks': v.unit,
            'pitch_period_steps': len(v.pitch_cycle), 'pitch_cycle': v.pitch_cycle, 'pitch_derivation': v.pitch_derivation,
            'note_layer_steps': len(v.layer), 'full_span_steps': len(v.velocities),
            'accent_phase_steps': v.phase, 'accents': dict(v.accents),
            'velocity_state_table': dict(v.levels), 'notes': len(v.notes),
        } for v in plan.voices],
        'midi_sha256': {name: hashlib.sha256((directory / name).read_bytes()).hexdigest()
                        for name in expected_files(plan)},
    }


def verify_manifest(plan, directory):
    directory = Path(directory).resolve()
    data = json.loads((directory / 'render.json').read_text())
    expected = json.loads(json.dumps(manifest(plan, directory)))
    if not isinstance(data, dict) or set(data) != set(expected):
        raise ValueError('render.json has missing or unknown fields')
    for key in expected:
        if key != 'rendered_at_utc' and data[key] != expected[key]:
            raise ValueError(f'render.json differs from the current plan/runtime: {key}')
    try:
        timestamp = datetime.fromisoformat(data['rendered_at_utc'])
        if timestamp.utcoffset() != timezone.utc.utcoffset(timestamp):
            raise ValueError('Timestamp must use UTC')
    except (TypeError, ValueError) as exc:
        raise ValueError('render.json has an invalid UTC timestamp') from exc
    return True


def publish(plan, output):
    """Verify a temporary render, then replace ordinary files in a real folder.

    Only this plan's filenames and render.json are replaced. Unrelated files stay.
    Each replacement is atomic; all files together are not a transaction. Run one
    renderer at a time and rerun after an interrupted publication.
    """
    output = Path(output).absolute()
    if output.is_symlink() or (output.exists() and not output.is_dir()):
        raise ValueError('Output must be an ordinary directory')
    output.mkdir(parents=True, exist_ok=True)
    names = (*expected_files(plan), 'render.json')
    for name in names:
        path = output / name
        if path.is_symlink() or (path.exists() and not path.is_file()):
            raise ValueError(f'Cannot replace a non-regular output file: {path}')
    with tempfile.TemporaryDirectory(prefix='.midi-stage-', dir=output.parent) as temporary:
        stage = Path(temporary)
        write_files(plan, stage)
        verify_files(plan, stage)
        (stage / 'render.json').write_text(json.dumps(manifest(plan, stage), indent=2) + '\n')
        verify_manifest(plan, stage)
        for name in names:  # Manifest last, so an interrupted render is detectable.
            destination = output / name
            if destination.is_file() and destination.read_bytes() == (stage / name).read_bytes():
                continue
            os.replace(stage / name, destination)
    verify_files(plan, output)
    verify_manifest(plan, output)
    return output
