# class Texture(Composition)

## def set_notes_data(self):

Each binary lists's form is repeated a number of times relative
to the duration of each grid unit for that repitition.

The ratio of repititions is set by determining the factors of ```len(self.binary)```

Each factor is used to multiply the number of repitions as well as the length of that iteration's durational value.

<img src="./images/example1.png" alt="set_notes_data loop" width="400">

This is a visualization shows how for every element belonging to the Texture object's  ```self.binary``` attribute there is a corresponding iteration over the object's ```self.factors``` attributes.

<img src="./images/example2.png" alt="set_notes_data loop" height="400">

Each row of this diagram represents a separate version of ```self.binary``` where the number of repititions cooresponds to the ``notes_data`` duration value. The ```set_notes_data``` method repeats the binary form for each factor of ```len(self.binary)```. The method also sets the durational value of each note so that the number of repititions and duration of each note equals the same length across versions of ```self.binary```.

In this way, ```set_notes_data``` combines each version of a single iteration over ```self.binary``` with every subsequent element of ```self.binary```. For each binary form there is a part that corresponds to each factor of ```len(self.binary)```. ```set_notes_data``` returns the combination of each part with each binary form, resulting in the total number of parts being equal to (number of factors) * (number of binary forms).