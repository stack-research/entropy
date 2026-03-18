"""Tests for the Arrow of Time setup."""

import sys
import os
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.arrow import BACKWARD_PREP_STEPS, build_arrow_systems


class TestArrowSystems:

    def test_build_arrow_systems_creates_reversed_system(self):
        np.random.seed(0)
        forward, backward = build_arrow_systems((160, 88), n_particles=80)

        assert forward.time_direction == 1
        assert backward.time_direction == -1
        assert backward.entropy_normalized() > forward.entropy_normalized()

    def test_reversed_system_returns_toward_low_entropy(self):
        np.random.seed(0)
        _, backward = build_arrow_systems((160, 88), n_particles=80)
        start_entropy = backward.entropy_normalized()

        for _ in range(BACKWARD_PREP_STEPS):
            backward.step()

        end_entropy = backward.entropy_normalized()
        assert end_entropy < start_entropy
