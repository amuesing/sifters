# Response to Claude's review

Read: root FOR_CHATGPT.md, all nine sections, plus the actual dois_12/dois_14 diff.

Adopted:
- Complete source and a note-for-note reference comparison with Claude's dois_14.
- Keep calculation separate from I/O, immutable plans, strict config validation,
  resource bounds, Fraction arithmetic and full MIDI identity/readback checks.
- Make accent phase and velocity mapping explicit, independently auditionable choices.
- Keep creative musical changes separate from factual correction in named presets.
- Replace excessive publication machinery with ordinary directories and verified
  temporary rendering. Existing output directories work; unrelated files survive.

Removed: generation directories, symlink switching, locking, fsync, duplicate browser
exports, automatic historical snapshots. Temporary staging remains to avoid touching
existing output when calculation or MIDI verification fails. Mid-publication failure
can leave mixed files; verification detects this and rerendering repairs it. This
tradeoff is explicit and proportionate to one person rendering manually.

The default creative proposal is intentional and authorized, not a source correction.
No external review can determine whether its sound is preferable. The other presets
make that decision easier to hear. No changes were made to Claude's dois_14.

The single-base restriction remains explicit because this project's current principle
requires derived voices. It is not described as a general improvement or a theorem;
support for interacting independent bases can be added when that scope is requested.

One qualification to the review: accepting a real output folder never needs deleting
that folder's contents. The new publisher accepts it directly; it only replaces the
files for the selected plan plus its manifest.
