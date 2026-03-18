"""Tests for the Maxwell's Demon module mechanics."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
