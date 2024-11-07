import matplotlib.pyplot as plt
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
generated_sequence = sieve_object.segment()  # Get the generated sequence
print("Generated sequence:", generated_sequence)

# Visualization
# max_value = max(generated_sequence) if generated_sequence else 0  # Use the max value from generated sequence
max_value = 15

# Create a list of x values that cover every integer from 0 to the max_value
x = list(range(0, max_value + 1))

# Create a y list with zeros for the number line
y = [0] * len(x)

plt.figure(figsize=(10, 2))  # Create a figure with specific size
plt.plot(x, y, 'o')  # Plot the points as circles on the x-axis

# Set x-axis limits to show every integer on the axis
plt.xlim(-1, max_value + 1)  # Set x-axis limits
plt.ylim(-1, 1)  # Set y-axis limits
plt.yticks([])  # Remove y-axis ticks
plt.xticks(range(max_value + 1))  # Set x-ticks to be every integer from 0 to max_value
plt.xlabel('Index')  # Label x-axis
plt.title('Number Line for Generated Sequence')  # Add title
plt.grid(True)  # Optional: Add a grid

# Highlight the points in the generated sequence
plt.plot(generated_sequence, [0] * len(generated_sequence), 'ro', markersize=8, label='Generated Sequence')  # Highlight generated points in red
plt.legend()  # Show legend
plt.show()  # Display the plot