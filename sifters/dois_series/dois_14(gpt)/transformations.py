"""Operations on integer-indexed onset cells, before assignment of time units."""
import numpy as np


def apply(relationship, sources, config):
    if relationship == 'complement':
        return 1 - sources[0]
    if relationship == 'retrograde':
        return sources[0][::-1]
    if relationship == 'shift':
        return np.roll(sources[0], config['shift_amount'])
    if relationship == 'augmentation':
        # Cell expansion, not a held note: [1,0] -> [1,1,0,0] for factor 2.
        return np.repeat(sources[0], config['factor'])
    if relationship == 'intersection':
        return np.bitwise_and.reduce(sources)
    if relationship == 'union':
        return np.bitwise_or.reduce(sources)
    raise ValueError(f'Unknown relationship: {relationship!r}')
