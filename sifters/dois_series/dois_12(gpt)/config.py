"""Musical configuration. Rendering never mutates these objects."""
from pathlib import Path

TITLE = 'dois_12(gpt)'
OUTPUT_DIR = Path(__file__).resolve().parent / 'mid'
TICKS_PER_QUARTER_NOTE = 480
TEMPO_BPM = 120
DURATION_MULTIPLIER_KEY = {
    'Whole Note': 4, 'Half Note': 2, 'Quarter Note': 1,
    'Eighth Note': 0.5, 'Sixteenth Note': 0.25, 'Thirty-Second Note': 0.125,
}
MIN_VELOCITY = 1
MAX_VELOCITY = 127
UNACCENTED_VELOCITY = 64
GATE_RATIO = 1.0
DRUM_RACK_BASE = 36
MAX_METER_NUMERATOR = 99
# None derives one shared meter; (4, 4) explicitly overrides it if it fits.
METER_OVERRIDE = None

# Preserve dois_12's actual sound while naming its two policy choices honestly.
# 'follow_shift': shift the field by each voice's accumulated canon offset.
# 'fixed': all voices sample the field at their own unshifted step indices.
ACCENT_PHASE_POLICY = 'follow_shift'
# Each grid ranks its own accent combinations by rarity. D's mapping differs.
VELOCITY_POLICY = 'per_grid_rarity'

# Static weather: each expression's true period must divide EVERY voice layer.
# These definitions are transcribed from Psappha; changing the base expression
# does not automatically rewrite the weather or the span residue source.
WEATHER = {'sieve5': '5@1|5@3', 'sieve8': '8@0|8@1|8@2|8@5|8@6'}
SPAN_RESIDUE_SOURCE = (0, 1, 7)
INSTRUMENT_CONFIGS = [
    {'name': 'A', 'sieve': '(8@0|8@1|8@7)&(5@1|5@3)|((8@0|8@1|8@2)&5@0)|((8@5|8@6)&(5@2|5@3|5@4))',
     'duration': 'Sixteenth Note'},
    {'name': 'B', 'derives_from': 'A', 'relationship': 'complement',
     'duration': 'Sixteenth Note'},
    {'name': 'C', 'derives_from': 'A', 'relationship': 'shift', 'shift_amount': 13,
     'duration': 'Sixteenth Note'},
    {'name': 'D', 'derives_from': ['A', 'C'], 'relationship': 'intersection',
     'step_ticks': 160},
]

# Explicit resource limits, checked before expanding periods/events.
MAX_STEPS = 100_000
MAX_EVENTS = 1_000_000
MAX_VOICES = 32
MAX_ACCENTS = 6  # plus one span accent: at most 128 ranked states


def settings():
    """Return an independent copy of all musical settings; no output paths."""
    from copy import deepcopy
    return deepcopy({name: value for name, value in globals().items()
                     if name.isupper() and name != 'OUTPUT_DIR'})
