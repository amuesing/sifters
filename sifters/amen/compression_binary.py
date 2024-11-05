from music21 import sieve

# Example binary sequence
binary_sequence = [0, 1, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1]

# Convert binary sequence to a list of positions where 1s occur
positions = [index for index, value in enumerate(binary_sequence) if value == 1]

# Create a CompressionSegment from these positions
compressed_sieve = sieve.CompressionSegment(positions)

# Output the derived sieve string
print(f"Derived sieve string: {str(compressed_sieve)}")

# To verify, generate a segment using the derived sieve string
sieve_object = sieve.Sieve(str(compressed_sieve))
print("Generated binary segment:", sieve_object.segment(segmentFormat='binary'))