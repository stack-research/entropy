"""Physical constants and unit conventions.

Natural units (simulation engine): k_B = 1, m = 1. Use :data:`K_B_NATURAL`.

SI units: use :data:`K_B_SI` for real-world thermodynamic estimates (e.g. Landauer).

Entropy quantities by module (what is displayed or compared):

- **box**, **arrow**: configurational entropy from spatial coarse-graining
  (:meth:`core.engine.ParticleSystem.configurational_entropy_spatial`); not
  full phase-space entropy unless velocity bins are added.
- **demon**: two-chamber configurational term plus a log-T **thermal proxy**
  for speed sorting (see :class:`modules.demon.DemonSystem`).
- **heatdeath**: status line reads from a :class:`modules.heatdeath.CosmologicalToyEngine`
  wrapping :class:`core.engine.ParticleSystem`; cooling and culling are
  non-Hamiltonian narrative layers on top of the same integrator.
- **selfentropy**: Landauer and dissipation use :data:`K_B_SI` and room T in kelvin.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

# Natural units (ParticleSystem, demon bookkeeping in k_B=1)
K_B_NATURAL = 1.0

# CODATA 2018 / SI (Joules per kelvin)
K_B_SI = 1.380649e-23

# Reference environment for self-entropy display (kelvin)
T_ROOM = 300.0


@dataclass(frozen=True)
class SimulationParams:
    """Default knobs shared across demos; pass into :class:`core.engine.ParticleSystem`."""

    dt: float = 1.0
    grid_shape: Tuple[int, int] = (8, 8)
    temperature: float = 1.0
    collision_radius: float = 3.0
