# Sifters
Sifters is a tool for developing musical compositions that makes use of combinatorial sieves as the point of departure for generative processes. My goal in coding Sifters has been to create a system for generating musical forms that are derived from a single logical source. The mechanism which hold that logic is called a 'sieve' and is a concept I inherited from my analysis of the score <i>Psappha</i> (1975) by Iannis Xenakis. The user is able to serialize the resulting intervalic structure by Prime, Inversion, Retrograde, and Retrograde-Inversion forms, as well as select from NonPitched, Monophonic, Homophonic, Heterophonic, and Polyphonic textures as a contrapuntal representation of the sieve.
# Controllers
# Generators
## class Composition:
## class Score(Composition):
## class Texture(Composition):
### def set_notes_data(self):
Each binary list's form is repeated a number of times relative
to the duration of each grid unit for that repitition.

The ratio of repititions is set by determining the factors of ```len(self.binary)```.

Each factor is used to multiply the number of repitions as well as the length of that iteration's durational value.

<img src="./images/example1.png" alt="set_notes_data loop" width="400">

This is a visualization shows how for every element belonging to the Texture object's ```self.binary``` attribute there is a corresponding iteration over the object's ```self.factors``` attributes.

<img src="./images/example2.png" alt="set_notes_data loop" height="400">

Each row of this diagram represents a separate version of ```self.binary``` where the number of repititions cooresponds to the ``notes_data`` duration value. The ```set_notes_data``` method repeats the binary form for each factor of ```len(self.binary)```. The method also sets the durational value of each note so that the number of repititions and duration of each note equals the same length across versions of ```self.binary```.

In this way, ```set_notes_data``` combines each version of a single iteration over ```self.binary``` with every subsequent element of ```self.binary```. For each binary form there is a part that corresponds to each factor of ```len(self.binary)```. ```set_notes_data``` returns the combination of each part with each binary form, resulting in the total number of parts being equal to (number of factors) * (number of binary forms).

### def generate_midi_pool(self, binary_index, factor_index):
For each j iteration returns a list of midi values called ```midi_pool```. Each ```midi_pool``` contains the exact amount of midi information required for the k loop (which is equal to ```len(self.closed_intervals[binary_index]) * self.factors[factor_index]```).

The method generates a serial matrix off of ```self.closed_intervals[binary_index]```. The method then utilizes the ```get_sucessive_diff``` to calculate the difference between successive intervals and appends that value to a list as either a positve or negative integer.

<img src="./images/example3.png" alt="set_notes_data loop" height="600">

In the example above we are given a list of steps which represent the successive differences in values of ```self.closed_intervals[binary_index]```. Ascending values between intervals are represented by a positive integer, and descending values between intervals are represented by a negative integer. This diagram displays the first two transformations of a midi sequence.

The ```generate_midi_pool``` method 
## class NonPitched(Texture):
## class Monophonic(Texture):
## class Homophonic(Texture):
## class Heterophonic(Texture):
## class Polyphonic(Texture):
# Transformers