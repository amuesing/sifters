"""The calculated data for one voice, separate from the composition settings."""
from dataclasses import dataclass

import numpy as np


@dataclass
class Voice:
    """One pitch mode's notes, shared velocities, timing, and derived accent expressions."""
    name: str
    notes: list[list[int]]
    velocities: np.ndarray
    step_ticks: int
    accents: dict[str, str]
