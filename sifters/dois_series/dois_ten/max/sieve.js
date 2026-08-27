autowatch = 1;
inlets  = 1;  // beat position (float) from [transport]
outlets = 2;  // 0: pitch, 1: velocity

// ---------------------------------------------------------------------------
// Precomputed from Python — dois_ten sieve binaries and velocity profiles
// ---------------------------------------------------------------------------

var vel_A = [127,127,0,0,0,0,0,0,63,0,127,0,0,127,63,0,127,0,0,0,0,0,127,1,0,127,0,0,0,63,0,127,0,127,0,0,0,127,63,0];
var vel_B = [0,0,64,64,64,64,64,64,0,64,0,64,64,0,0,64,0,64,64,64,64,64,0,0,64,0,64,64,64,0,64,0,64,0,64,64,64,0,0,64];
var vel_C = [0,0,63,0,127,0,127,0,0,0,127,63,0,127,127,0,0,0,0,0,0,63,0,127,0,0,127,63,0,127,0,0,0,0,0,127,1,0,127,0];
var vel_D = [0,0,0,0,0,0,0,0,0,0,64,0,0,64,64,0,0,0,0,0,0,0,0,64,0,0,0,0,0,64,0,0,0,0,0,0,0,0,64,0];

// Drum Rack pad pitches — one pad per voice
var PITCH_A = 36; // C1
var PITCH_B = 37; // C#1
var PITCH_C = 38; // D1
var PITCH_D = 39; // D#1

// Step sizes in ticks (480 ticks = 1 quarter note)
var STEP_ABC = 120; // sixteenth note
var STEP_D   = 160; // triplet eighth note
var PERIOD   = 40;

// Track which step each voice is on to detect crossings
var last_step_ABC = -1;
var last_step_D   = -1;

// ---------------------------------------------------------------------------
// Called on every bang from the metro — receives current beat position
// ---------------------------------------------------------------------------

function msg_float(beats) {
    var ticks = Math.floor(beats * 480);

    var step_ABC = Math.floor(ticks / STEP_ABC) % PERIOD;
    var step_D   = Math.floor(ticks / STEP_D)   % PERIOD;

    // Fire A, B, C — they share the same grid
    if (step_ABC !== last_step_ABC) {
        last_step_ABC = step_ABC;
        fireNote(PITCH_A, vel_A[step_ABC]);
        fireNote(PITCH_B, vel_B[step_ABC]);
        fireNote(PITCH_C, vel_C[step_ABC]);
    }

    // Fire D — triplet-eighth grid, independent of A/B/C
    if (step_D !== last_step_D) {
        last_step_D = step_D;
        fireNote(PITCH_D, vel_D[step_D]);
    }
}

function fireNote(pitch, velocity) {
    if (velocity <= 0) return;
    // Send velocity first (right inlet of noteout), then pitch (left inlet triggers output)
    outlet(1, velocity);
    outlet(0, pitch);
}

// Reset step tracking when transport stops or loops
function reset() {
    last_step_ABC = -1;
    last_step_D   = -1;
}
