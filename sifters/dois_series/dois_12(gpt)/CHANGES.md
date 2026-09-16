# Changes from dois_12

Created 11 September 2026 in response to the audit in `REVIEW.md`.

## Implemented

1. **Safe publication:** render and verify a new complete generation, then switch `mid` atomically. Preserve previous generations and unrelated user files. Reject real existing output directories instead of deleting or migrating them implicitly. Serialize publishers with an OS file lock.
2. **Full output verification:** compare every decoded note to the planned onset/duration/channel/pitch/velocity data in every format. Reconstruct silence through the actual end boundary and test distinct passes/minimal periods using the decoded files.
3. **MIDI integrity:** validate channel-aware note lifecycles, orphan releases, overlaps, hanging notes, type, PPQ, metadata and timing, exact track inventory, and extra pads/events.
4. **First convergence:** enforce static weather and exact equality with the raw rhythmic parity. Never expand the piece to accommodate an incompatible accent modulus.
5. **Augmentation:** transform a minimal onset layer once, then tile the transformed result. A complete feasible augmented composition is tested. A configuration can still be rejected if its accents cannot distinguish all required passes.
6. **Provenance:** complete configuration identity, resolved accent tables, dependency/source/file hashes, and a manifest. Separate timestamp from deterministic MIDI metadata.
7. **Strict inputs:** names, pads, duration/step units, gates, relationship arity, sources, factors, and period/resource limits. Derive pad assignments without mutating the configuration module.
8. **Structure and workflow:** calculation and MIDI I/O are separate; robust local module loading; dry-run, verification-only, output-path option; pinned dependencies; persistent regression tests.
9. **Meter:** a real override is available. Automatic selection retains 40/16 for the baseline; 4/4 fits without changing note events.

## Sound preserved and policies documented

The baseline contains exactly the original 238 notes, including velocities and gate lengths, at 19,200 ticks. C retains its shifted accent field. D retains its per-grid rarity mapping. The policy names explicitly describe what the code does; this version does not claim identical velocity maps across grids.

Fixed weather is a supported alternative policy, but the default source/residues with fixed weather produce repeated passes in C. That combination is correctly rejected. Changing this sound requires a deliberate new accent design.

Historical iterations and the parked Max patch are not changed. Form remains in the DAW. Shared-clause symbolic extraction, a new common velocity-table policy, a plugin port, and automatic old-generation cleanup are not implemented.

## Validation

The persistent unittest suite covers the audit reproductions: missing and duplicated final passes across all outputs, wrong note-off channels, ensemble tempo/PPQ changes, extra pads/tracks, parity overshoot, augmentation, trailing rests, invalid settings, write/verification/pointer failures, preservation of foreign files and previous generations, provenance changes, deterministic MIDI, meter/gate options, and resource limits. The frozen baseline fixture was produced by the independent MIDI byte decoder used for the original audit.

The baseline was also compared directly against the existing `dois_12` files after building the new variant. File bytes differ because the title and provenance are new; note events are identical.
