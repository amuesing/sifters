from music21 import sieve

# Create a sieve with a simple logical structure
a = sieve.Sieve('(2@0&-64@58)')

# Generate a binary segment from the sieve
binary_segment = a.segment(segmentFormat='binary')

# Output the result
print(binary_segment)