"""Tests for the Maxwell's Demon module mechanics."""

import numpy as np

from modules.demon import DemonSystem


class TestDemonSystem:

    def test_closed_gate_blocks_wall_tunneling(self):
        s = DemonSystem(1, (100, 100))
        wx = s.wall_x
        y = (s.gate_y_min + s.gate_y_max) / 2.0

        s.gate_open = False
        s.pos[0] = [wx - 1.0, y]
        s.vel[0] = [5.0, 0.0]

        s.step()

        assert s.pos[0, 0] < wx
        assert s.vel[0, 0] < 0.0

    def test_open_gate_allows_crossing(self):
        s = DemonSystem(1, (100, 100))
        wx = s.wall_x
        y = (s.gate_y_min + s.gate_y_max) / 2.0

        s.gate_open = True
        s.pos[0] = [wx - 1.0, y]
        s.vel[0] = [5.0, 0.0]

        s.step()

        assert s.pos[0, 0] > wx
        assert s.vel[0, 0] > 0.0

    def test_chamber_temperature_is_half_mean_v_squared(self):
        s = DemonSystem(1, (200, 200))
        s.pos[0] = [50.0, 100.0]
        s.vel[0] = [2.0, 2.0]
        _, _, t_left, _ = s.chamber_stats()
        # T = <v^2>/2 in 2D, m=k_B=1
        assert abs(t_left - 4.0) < 1e-6  # (4+4)/2 = 4
