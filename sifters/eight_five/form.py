"""The form: the sieve read again, one section per step of its period. dois_44.

Until now the piece was one parity statement — 19,200 ticks, 20 seconds at 120 BPM — and
form was left to the DAW. dois_09 tried a form in code (5 movements x 8 sections = 40),
but which voices played where came from density thresholds written by hand. Here it comes
from the sieve the same way the rhythm does:

    section s, for s = 0 .. P - 1, is one whole parity statement, and voice X plays in it
    exactly when X's note layer has an attack at step s.

So the form is the rhythm again, one level up: A plays in the 27 sections where the
sieve has a member and B in the 13 where it has none — they never share a section, as
they never share a step — C in the sections 13 later, D where A and C both play.
Principle I asks a duration to state the sieve's period; 40 sections state it once more.
At 120 BPM that is 40 x 20 seconds, thirteen minutes and twenty seconds.

Nothing may repeat identically, and two sections with the same voices would repeat the
same statement. So each section reads the lattice s steps further on: the note a voice
plays at step n of section s is the note its mode gives step n + s. In the lattice that
is a transposition by 13 x s mod 40, all 40 different — in the 40-step tuning a chain of
major thirds through every pitch class, closing as the form closes. The static set has
no pitch to move, so its sections WOULD repeat, and it gets no form.

Each voice's statement inside a section is exactly its parity statement: same onsets,
lengths and velocities. Only its presence and its transposition are the form's.
"""
import math

import config
from accents import notes_for_steps
from midi import make_track, save_tracks, voice_events


def form_sections(note_layers):
    """How many sections: the period the voices' layers share — 40 for psappha."""
    return math.lcm(*note_layers.values())


def form_presence(base_binaries, sections):
    """Which sections each voice plays in: its own note layer, read one step per section."""
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
