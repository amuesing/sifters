"""The form: the sieve read again, one section per step of its period.

Section s, for s = 0 .. P - 1, is one whole parity statement, and voice X plays in it
exactly when X's note layer has an attack at step s. The form is the rhythm again, one
level up: A plays in the 27 sections where the sieve has a member and B in the 13 where
it has none, C in the sections 13 later, D where A and C both play. 40 sections state
the period once more (Principle I): 40 x 20 seconds at 120 BPM, 13'20".

Two sections with the same voices would repeat (Principle III), so each reads the
lattice s steps further on: the note a voice plays at step n of section s is the note
its mode gives step n + s. In the lattice that is a transposition by 13 x s mod 40, all
40 different. The static set has no pitch to move, so it gets no form.
"""
import math

import config
from accents import notes_for_steps
from midi import make_track, save_tracks, voice_events


def form_sections(note_layers):
    """How many sections: the period the voices' layers share, 40 for psappha."""
    return math.lcm(*note_layers.values())


def form_presence(base_binaries, sections):
    """Which sections each voice plays in: its own note layer, one step per section."""
    return {name: [int(binary[s % len(binary)]) for s in range(sections)]
            for name, binary in base_binaries.items()}


def write_form(voices, notes_for, note_layers, base_binaries, parity, meter, prefix,
               stamp):
    """`<prefix>_form.mid`: one track per voice, a parity statement per section."""
    sections = form_sections(note_layers)
    present = form_presence(base_binaries, sections)
    total = sections * parity
    by_name = {cfg['name']: cfg for cfg in config.INSTRUMENT_CONFIGS}
    tracks = []
    for channel, voice in enumerate(voices):
        note_at = notes_for(by_name[voice.name], note_layers)
        events = []
        for section in range(sections):
            if not present[voice.name][section]:
                continue
            notes = notes_for_steps(voice.velocities,
                                    lambda step, s=section: note_at(step + s))
            start = section * parity
            events += [(tick + start, kind, pitch, velocity, chan) for tick, kind, pitch,
                       velocity, chan in voice_events(notes, voice.velocities,
                                                      voice.step_ticks, parity, channel)]
        line = f"{stamp} voice={voice.name} form={sections} sections"
        tracks.append(make_track(voice.name, events, total, meter, line))
    played = {name: sum(flags) for name, flags in present.items()}
    save_tracks(tracks, f"{prefix}_form", total, meter,
                note=f", {sections} sections of {parity} ticks — sections per voice "
                     + ", ".join(f"{n} {k}" for n, k in played.items()))
    return f"{prefix}_form"
