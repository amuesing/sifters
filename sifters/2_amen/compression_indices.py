from music21 import sieve

# Define the list of indices
indices = [4, 7, 9, 12, 15]

# Use CompressionSegment to derive a sieve pattern
compressed_sieve = sieve.CompressionSegment(indices)

# Print out the derived sieve notation
print("Derived compression sieve string:", str(compressed_sieve))

# Optionally apply z range
apply_z_range = True  # Set this to False if you don't want to apply z range

if apply_z_range:
    # Set z range to encompass only the input values
    min_z = min(indices)
    max_z = max(indices)
    z_range = list(range(min_z, max_z + 1))  # Create a list of values from min to max
    print(f"Applying z range: {z_range}")
else:
    print("Skipping z range application.")

# Generate a sieve object
sieve_object = sieve.Sieve(str(compressed_sieve))

# Apply z range if specified
if apply_z_range:
    sieve_object.setZ(z_range)

# Print the generated sequence (with or without z range)
print("Generated sequence:", sieve_object.segment())