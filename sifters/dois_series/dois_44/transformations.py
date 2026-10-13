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
    """Augmentation: every step lasts `factor` steps, so an attack is followed by rests.

    Until dois_41 this was `np.repeat`, which turned each attack into `factor`
    consecutive attacks — [1, 0, 1] by 2 became [1, 1, 0, 0, 1, 1], a roll rather than
    an augmentation, doubling the attack count. Nothing in a composition used it, so
    no rendered note changed; the onsets now land where augmentation puts them.
    """
    stretched = np.zeros(len(binary) * factor, dtype=np.asarray(binary).dtype)
    stretched[::factor] = binary
    return stretched

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
