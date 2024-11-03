from music21 import sieve

a = sieve.Sieve('1@0')
# a.segment()

print(a.segment())  # Should contain all even numbers excluding 58