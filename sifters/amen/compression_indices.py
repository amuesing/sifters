from music21 import sieve

# Define the list of indexes
indexes = [4, 7, 9, 12, 15]

# Use CompressionSegment to derive a sieve pattern
compressed_sieve = sieve.CompressionSegment(indexes)

# Print out the derived sieve notation
print("Sieve string:", str(compressed_sieve))

# Verify by generating a sequence from the derived sieve
sieve_object = sieve.Sieve(str(compressed_sieve))
print("Generated sequence:", sieve_object.segment())