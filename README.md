# Sifters

Sifters is a 'Data Synthesizer' used for developing musical compositions that makes use of logical sieves as the point of departure for creative processes. My goal in coding Sifters has been to create a system for synthesizing data to generate musical forms that are derived from a single logical source. The mechanism which holds that logic is called a 'sieve', and its use to derive musical materials is a concept inherited from the analysis of the score to *Psappha* (1975) by Iannis Xenakis.

The logical sieve behaves in a way that is similar to an oscillator from a traditional analogue synthesizer configuration. Sifters is designed to output MIDI, Scala, and Wav files, which can then be incorporated into a Digital Audio Workstation (DAW). For convenience, I have optimized Sifters around both Ableton Live’s use of MIDI clips and Serum: Advanced Wavetable Synthesizer's use of WAV files in the construction of wavetables.

## Usage

To use Sifters, create a `Composition` object with the following arguments:

- `sieve`: A string that can be used to initialize a sieve object from the music21 library. This string represents the logical sieve from which musical materials will be derived. For more information on how the sieve object works, refer to the [music21 documentation](https://web.mit.edu/music21/doc/moduleReference/moduleSieve.html).

- `grid_set`: This parameter accepts a list of fraction objects that define the basic unit of duration for each version of the sieve. If none are provided, Sifters will generate a list of grids based on the percent of the period the non-zero integers fall on in the binary representation of the sieve. Essentially, this parameter allows users to specify the rhythmic structure or grid divisions for the generated musical materials, providing flexibility in crafting rhythmic patterns and structures.

- `normalized_grids`: A boolean value that, if assigned as true, will repeat each `grid_set` so that each grid is the same length. This ensures that all grids have a consistent duration, which can be useful for maintaining rhythmic coherence in the generated musical output.
