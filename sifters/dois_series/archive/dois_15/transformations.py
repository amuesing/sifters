"""Binary operations on sieve segments.

These are the vocabulary `build_binary` derives voices with. Keeping them here and
dispatching to them by name — rather than writing `1 - src` and `np.roll(...)` inline —
means a new relationship is added in one place, and the derivation reads as what it is.
"""
import numpy as np

def invert_binary(binary):
    """Complement: every step the source does NOT occupy."""
    return 1 - binary

def reverse_binary(binary):
    """Retrograde."""
    return binary[::-1]

def stretch_binary(binary, factor):
    """Augmentation: each step becomes `factor` steps."""
    return np.repeat(binary, factor)

def shift_binary(binary, shift_amount):
    """Canon: the same pattern, delayed."""
    return np.roll(binary, shift_amount)

def intersect_binaries(binaries):
    """Convergence: only where every source sounds together."""
    result = binaries[0].copy()
    for b in binaries[1:]:
        result = result & b
    return result

def union_binaries(binaries):
    """Every step any source occupies."""
    result = binaries[0].copy()
    for b in binaries[1:]:
        result = result | b
    return result
