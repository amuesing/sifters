# Ableton browser export fix — 2026-09-13

Live's browser showed the iteration but omitted the symlinked mid folder. Normal
renders now automatically export verified ordinary MIDI files to mid-files/.
Four tests cover automatic CLI export, byte equality/updates, unrelated-file
preservation, corrupt source rejection and symlink destination rejection (44 total).
Musical notes and timing are unchanged. An import/playback symptom remains to be
specified; the renderer's own validation is not a DAW compatibility guarantee.

# Complete-sieve musical update

- Restore all four omitted Psappha terms: A now has 27 attacks per 40 steps.
- Keep A/B complementary at 120 ticks. Move C (+13) to 160 ticks.
- Change D to B intersect C at 240 ticks, preserving a sparse countervoice.
- Derive spans 32/32/3/16 and keep the first parity at 19200 ticks.
- Make the default accent phase fixed and implement shared_rarity: a single
  state table based on common weather weights and the rarest derived span.
- Preserve full gates, 1–127 velocity control, and the two clause-derived weather
  sieves. The new default intentionally changes notes and dynamics.
- Extend diagnostics with active steps, clock units, raw periods and policy names.
- Add complete-source/reference MIDI tests; keep legacy fixtures as explicit
  historical regression inputs. Forty tests pass.
- Preserve pre-update code/tests/MIDI in history/before-full-psappha.zip and retain
  the previous generated MIDI under .mid-renders/.

See MUSICAL_DESIGN.md for source attribution, comparisons and rationale.

---

# Historical entries below: superseded default music

# Changes from dois_12(gpt)

Created 11 September 2026. Default notes, velocities, gates, tempo and parity are
unchanged. Titles and engine provenance identify this as `dois_13(gpt)`.

1. Omit the unnecessary span accent for single-pass voices; honor
   `UNACCENTED_VELOCITY` when there are no accent layers.
2. Reject unknown and missing top-level configuration settings.
3. Check the complete manifest against the selected plan/current source and
   dependency versions, including resolved voice data and timestamp format.
4. Reuse fully verified identical generations. Repair damaged output instead of
   incorrectly reusing it; preserve prior generations and foreign files.
5. Add read-only musical diagnostics and identify repeated pass pairs in errors.
6. Expand the suite from 23 to 30 tests covering these changes, including
   weather-only single-pass voices and publication failure behavior after deduplication.

The fixed residue policy and per-grid velocity mapping remain deliberate musical
choices. Automatic history pruning, form generation and the Max patch remain outside
this iteration. The original audit remains in REVIEW.md for historical context.

---

## Inherited changes from dois_12

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
