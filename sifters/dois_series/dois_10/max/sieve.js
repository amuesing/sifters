autowatch = 1;
inlets  = 1;  // beat position (float) from [transport]
outlets = 2;  // 0: pitch, 1: velocity

// ---------------------------------------------------------------------------
// dois_ten — generated from mid/dois_ten_*_prime.mid, do not hand-edit
// ---------------------------------------------------------------------------
// Each voice carries its own velocity array, and the array's LENGTH is that voice's
// period in steps. A and C run 120 steps because their accent sieves include modulus
// 3, which does not divide the 40-step note layer: the accents land differently on
// each of three passes, so the voice does not fully state itself until step 120.
// B and D carry no accents and close after 40 steps. Positions are taken from
// absolute transport ticks, so every voice stays phase-locked to the piece start.

var TPQ = 480;

var VOICES = [
    {
        name:  "A",
        pitch: 36,          // Drum Rack pad 1
        step:  120,          // ticks per step
        // 120 steps = one full statement (3 iterations of the 40-step note layer)
        vel: [
            127,127,0,0,0,0,0,0,63,0,127,0,0,127,63,0,127,0,0,0,0,0,127,1,0,127,0,0,0,63,0,127,0,127,0,0,0,127,63,0,127,127,0,0,0,0,0,0,127,0,127,0,0,63,127,0,127,0,0,0,0,0,63,94,0,127,0,0,0,127,0,32,0,127,0,0,0,63,127,0,127,127,0,0,0,0,0,0,127,0,127,0,0,127,127,0,127,0,0,0,0,0,127,94,0,127,0,0,0,127,0,127,0,63,0,0,0,127,127,0
        ],
        last: -1
    },
    {
        name:  "B",
        pitch: 37,          // Drum Rack pad 2
        step:  120,          // ticks per step
        // 40 steps = one full statement (1 iteration of the 40-step note layer)
        vel: [
            0,0,64,64,64,64,64,64,0,64,0,64,64,0,0,64,0,64,64,64,64,64,0,0,64,0,64,64,64,0,64,0,64,0,64,64,64,0,0,64
        ],
        last: -1
    },
    {
        name:  "C",
        pitch: 38,          // Drum Rack pad 3
        step:  120,          // ticks per step
        // 120 steps = one full statement (3 iterations of the 40-step note layer)
        vel: [
            0,0,127,0,127,0,63,0,0,0,127,127,0,127,127,0,0,0,0,0,0,63,0,127,0,0,127,63,0,127,0,0,0,0,0,127,1,0,127,0,0,0,63,0,127,0,127,0,0,0,127,63,0,127,127,0,0,0,0,0,0,127,0,127,0,0,63,127,0,127,0,0,0,0,0,63,94,0,127,0,0,0,127,0,32,0,127,0,0,0,63,127,0,127,127,0,0,0,0,0,0,127,0,127,0,0,127,127,0,127,0,0,0,0,0,127,94,0,127,0
        ],
        last: -1
    },
    {
        name:  "D",
        pitch: 39,          // Drum Rack pad 4
        step:  160,          // ticks per step
        // 40 steps = one full statement (1 iteration of the 40-step note layer)
        vel: [
            0,0,0,0,0,0,0,0,0,0,64,0,0,64,64,0,0,0,0,0,0,0,0,64,0,0,0,0,0,64,0,0,0,0,0,0,0,0,64,0
        ],
        last: -1
    }
];

// ---------------------------------------------------------------------------
// Called on every bang from the metro — receives current beat position
// ---------------------------------------------------------------------------

function msg_float(beats) {
    var ticks = Math.floor(beats * TPQ);

    for (var i = 0; i < VOICES.length; i++) {
        var v = VOICES[i];
        var step = Math.floor(ticks / v.step) % v.vel.length;
        if (step !== v.last) {
            v.last = step;
            fireNote(v.pitch, v.vel[step]);
        }
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
    for (var i = 0; i < VOICES.length; i++) VOICES[i].last = -1;
}
