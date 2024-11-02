from music21 import sieve

# Define two segments around 58
s1 = sieve.Sieve('2@0 & (29@2)')  # Generates even numbers up to 56
s2 = sieve.Sieve('2@0 & (28@30)')  # Generates even numbers starting from 60

# Combine them using union to skip over 58
combined_sieve = sieve.Sieve('2@0 | 58@0')
result = combined_sieve.segment()

print(result)  # Should contain all even numbers excluding 58