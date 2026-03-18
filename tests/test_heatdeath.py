"""Tests for Heat Death rendering robustness."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.heatdeath import StarField


class TestStarField:

    def test_small_terminal_sizes_do_not_crash(self):
        for rows, cols in ((1, 1), (2, 4), (3, 6), (4, 7)):
            field = StarField(rows, cols)
            for obj in field.objects:
                assert 0 <= obj['x'] < cols
                assert 0 <= obj['y'] < rows
