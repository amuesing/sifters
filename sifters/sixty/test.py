import os
import mido
import music21
import numpy
import glob

# --------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------
TITLE = 'sixty'
OUTPUT_DIR = f'sifters/{TITLE}/mid/'
TICKS_PER_QUARTER_NOTE = 480

DEFAULT_VELOCITY_PROFILE = {
    'gap': 64,
    'primary': 127,
    'secondary': 64,
    'overlap': 1
}

DURATION_MULTIPLIER_KEY = {
    'Whole Note': 4,
    'Half Note': 2,
    'Quarter Note': 1,
    'Eighth Note': 0.5,
    'Sixteenth Note': 0.25
}

DURATION_TO_DENOMINATOR = {
    'Whole Note': 1,
    'Half Note': 2,
    'Quarter Note': 4,
    'Eighth Note': 8,
    'Sixteenth Note': 16
}

INSTRUMENT_CONFIGS = [
    {
        'sieve': '(3@0|3@2)&(4@1|4@3)&(5@2|5@3)',
        'accent_dict': {
            'primary': '(5@2)',
            'secondary': '(5@3)',
        },
        'duration': 'Sixteenth Note',
        'note': 36,
    },
    {
        'sieve': '(10@0|12@0|15@0)',
        'accent_dict': {
            'primary': '(10@0)',
            'secondary': '(12@0)',
        },
        'duration': 'Sixteenth Note',
        'note': 37,
    },
    {
        'sieve': '(3@1|3@2)&(4@0|4@3)',
        'accent_dict': {
            'primary': '(3@2)',
            'secondary': '(4@3)',
        },
        'duration': 'Sixteenth Note',
        'note': 38,
    },
    {
        'sieve': '(4@2|4@3)&(5@1|5@4)&(6@0|6@5)',
        'accent_dict': {'primary': '(5@4)', 'secondary': '(6@5)'},
        'duration': 'Eighth Note',
        'note': 39,
    },
    {
        'sieve': '(4@0|4@1)&(5@2|5@3)&(6@4|6@5)',
        'accent_dict': {'primary': '(5@4)', 'secondary': '(6@5)'},
        'duration': 'Eighth Note',
        'note': 40,
    },
    {
        'sieve': '4@1&5@3&6|5',
        'accent_dict': {'primary': '(5@4)', 'secondary': '(6@5)'},
        'duration': 'Eighth Note',
        'note': 41,
    },
    {
        'sieve': '4@1&5@3&6@5',
        'accent_dict': {'primary': '(5@4)', 'secondary': '(6@5)'},
        'duration': 'Eighth Note',
        'note': 42,
    },
]

# --------------------------------------------------------------------
# Utility Functions
# --------------------------------------------------------------------
def ensure_directory(path):
    """Create the directory if it doesn't exist."""
    os.makedirs(path, exist_ok=True)

def clear_directory(path):
    """Delete all files in the specified directory."""
    for file_path in glob.glob(f'{path}*'):
        os.remove(file_path)

def sieve_to_binary(sieve_obj):
    """Convert a music21.sieve.Sieve object to a 1D numpy array of 0/1."""
    return numpy.array(sieve_obj.segment(segmentFormat='binary'))

def generate_time_signature(period, duration):
    """
    Return (numerator, denominator) for the time_signature event.
    The numerator is the 'period' (assuming it's <= 255).
    The denominator is deduced from the specified duration.
    """
    if period > 255:
        raise ValueError(f"The period {period} exceeds the maximum allowed value of 255.")
    return period, DURATION_TO_DENOMINATOR.get(duration, 16)

def get_duration_multiplier(duration_name):
    """
    Return the multiplier for how many quarter-note ticks each note should last.
    """
    return DURATION_MULTIPLIER_KEY.get(duration_name, 0.25)

def create_midi(binary, filename, velocities, note, duration_multiplier, time_signature):
    """
    Create a new MIDI file using Mido, with a single track,
    writing note_on/note_off messages according to 'binary' and 'velocities'.
    """
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)
    
    # Track name meta-message
    track.append(mido.MetaMessage('track_name', name=filename, time=0))
    
    # Time signature
    numerator, denominator = time_signature
    track.append(mido.MetaMessage('time_signature', numerator=numerator, denominator=denominator, time=0))
    
    duration_ticks = int(TICKS_PER_QUARTER_NOTE * duration_multiplier)
    
    # For each index in the binary array, if it's a "1", we play the note with velocity
    for is_on, vel in zip(binary, velocities):
        # If there's a "hit," we use the velocity; otherwise, velocity=0
        actual_velocity = vel if is_on else 0
        
        # Note on at the start of the slice
        track.append(mido.Message('note_on', note=note, velocity=actual_velocity, time=0))
        # Note off after duration_ticks
        track.append(mido.Message('note_off', note=note, velocity=actual_velocity, time=duration_ticks))
    
    # Save to .mid file
    filepath = os.path.join(OUTPUT_DIR, f"{filename}.mid")
    mid.save(filepath)

def create_accent_binaries(accent_dict, period):
    """
    Convert accent sieve patterns to binary arrays of length 'period'.
    If accent_dict has keys 'primary'/'secondary', parse them as separate Sieve objects.
    """
    # If pattern is None or empty, we fill with zeros.
    accent_binaries = {}
    for key, pattern in accent_dict.items():
        if pattern:
            accent_binaries[key] = sieve_to_binary(music21.sieve.Sieve(pattern))
        else:
            accent_binaries[key] = numpy.zeros(period)
    return accent_binaries

def accent_velocity(base_binary, primary_binary, secondary_binary, velocity_profile):
    """
    Combine base_binary with two accent layers (primary, secondary).
    Return an array of velocities, the same length as base_binary.
    """
    velocities = numpy.zeros(len(base_binary), dtype=int)
    for i, val in enumerate(base_binary):
        if val:  # There's a "hit" at this index
            # Check whether there's a primary or secondary accent at i
            p_hit = primary_binary[i % len(primary_binary)]
            s_hit = secondary_binary[i % len(secondary_binary)]
            
            if p_hit and s_hit:
                velocities[i] = velocity_profile['overlap']
            elif p_hit:
                velocities[i] = velocity_profile['primary']
            elif s_hit:
                velocities[i] = velocity_profile['secondary']
            else:
                velocities[i] = velocity_profile['gap']
    return velocities

def process_sieve(config):
    """
    Create and save a MIDI file from the given configuration.
    The filename is automatically generated from the sieve expression + duration.
    """
    sieve_str = config['sieve']
    sieve_obj = music21.sieve.Sieve(sieve_str)
    period = sieve_obj.period()
    
    # Ensure we cover the full period from 0 to period-1
    sieve_obj.setZRange(0, period - 1)
    
    # Base binary array
    base_binary = sieve_to_binary(sieve_obj)
    
    # Get accent dictionaries
    accent_binaries = create_accent_binaries(config.get('accent_dict', {}), period)
    primary_binary = accent_binaries.get('primary', numpy.zeros(period))
    secondary_binary = accent_binaries.get('secondary', numpy.zeros(period))
    
    # Velocity calculations
    velocity_profile = config.get('velocity_profile', DEFAULT_VELOCITY_PROFILE)
    velocities = accent_velocity(base_binary, primary_binary, secondary_binary, velocity_profile)
    
    # Other config data
    note = config.get('note', 64)
    duration = config.get('duration', 'Quarter Note')
    duration_multiplier = get_duration_multiplier(duration)
    time_signature = generate_time_signature(period, duration)
    
    # Generate filename (no sanitization)
    filename = f"{sieve_str}_{duration}"
    
    # Debug/log info
    print("Processing Sieve:", sieve_str)
    print("  --> Period =", period)
    print("  --> Duration =", duration)
    print("  --> Time Signature =", time_signature)
    print("  --> MIDI Filename =", filename + ".mid")
    
    # Create the MIDI file
    create_midi(base_binary, filename, velocities, note, duration_multiplier, time_signature)

def main():
    # Ensure the output directory exists, then clear it
    ensure_directory(OUTPUT_DIR)
    clear_directory(OUTPUT_DIR)
    
    # Process each config dictionary in the list
    for config in INSTRUMENT_CONFIGS:
        process_sieve(config)

if __name__ == '__main__':
    main()