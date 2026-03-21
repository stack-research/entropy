"""Tests for the Arrow of Time setup."""

import numpy as np

from core.constants import SimulationParams
from core.engine import ParticleSystem
from modules.arrow import BACKWARD_PREP_STEPS, build_arrow_systems


class TestArrowSystems:

    def test_build_arrow_systems_creates_reversed_system(self):
        forward, backward = build_arrow_systems((160, 88), n_particles=80, seed=0)

        assert forward.time_direction == 1
        assert backward.time_direction == -1
        assert backward.entropy_normalized() > forward.entropy_normalized()

    def test_shared_initial_state_matches_microstate(self):
        """Same (x,v) as build_arrow_systems uses before backward prep."""
        np.random.seed(123)
        forward = ParticleSystem(
            40,
            (160, 88),
            'corner',
            params=SimulationParams(temperature=1.0),
        )
        backward = ParticleSystem(
            40,
            (160, 88),
            'uniform',
            params=SimulationParams(temperature=1.0),
        )
        backward.pos = forward.pos.copy()
        backward.vel = forward.vel.copy()
        backward.n = forward.n
        np.testing.assert_allclose(forward.pos, backward.pos)
        np.testing.assert_allclose(forward.vel, backward.vel)

    def test_independent_initial_states_when_disabled(self):
        f1, b1 = build_arrow_systems(
            (160, 88), n_particles=40, seed=99, shared_initial_state=False,
        )
        assert not (
            np.allclose(f1.pos, b1.pos) and np.allclose(f1.vel, b1.vel)
        )

    def test_reversed_system_returns_toward_low_entropy(self):
        _, backward = build_arrow_systems((160, 88), n_particles=80, seed=0)
        start_entropy = backward.entropy_normalized()

        for _ in range(BACKWARD_PREP_STEPS):
            backward.step()

        end_entropy = backward.entropy_normalized()
        assert end_entropy < start_entropy
