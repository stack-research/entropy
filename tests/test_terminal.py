"""Tests for shared terminal-size guards."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.terminal import require_terminal_size


class FakeScreen:
    def __init__(self, rows, cols, key=-1):
        self.rows = rows
        self.cols = cols
        self.key = key
        self.calls = []

    def getmaxyx(self):
        return self.rows, self.cols

    def erase(self):
        self.calls.append('erase')

    def addstr(self, row, col, text, attr=0):
        self.calls.append(('addstr', row, col, text, attr))

    def refresh(self):
        self.calls.append('refresh')

    def getch(self):
        self.calls.append('getch')
        return self.key


class TestTerminalGuard:

    def test_returns_ok_when_terminal_is_large_enough(self):
        screen = FakeScreen(24, 80)
        assert require_terminal_size(screen) == 'ok'

    def test_returns_wait_when_terminal_is_too_small(self):
        screen = FakeScreen(8, 30, key=-1)
        assert require_terminal_size(screen) == 'wait'
        assert 'refresh' in screen.calls

    def test_returns_quit_when_user_presses_q(self):
        screen = FakeScreen(8, 30, key=ord('q'))
        assert require_terminal_size(screen) == 'quit'
