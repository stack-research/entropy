"""Terminal renderer. Braille dots for micro view, block characters for macro.
Looks like classified output from Los Alamos, 1962."""

import curses
import numpy as np


# Braille character encoding: each character is a 2x4 dot grid
# Dot positions map to bits in the Unicode braille range (U+2800)
#   Col 0  Col 1
#   0x01   0x08   row 0
#   0x02   0x10   row 1
#   0x04   0x20   row 2
#   0x40   0x80   row 3
BRAILLE_BASE = 0x2800
BRAILLE_MAP = (
    (0x01, 0x08),
    (0x02, 0x10),
    (0x04, 0x20),
    (0x40, 0x80),
)

# Block characters for macro density view (ascending density)
DENSITY_CHARS = ' ░▒▓█'

# Box drawing
BOX_TL = '┌'
BOX_TR = '┐'
BOX_BL = '└'
BOX_BR = '┘'
BOX_H = '─'
BOX_V = '│'


class BrailleCanvas:
    """Pixel buffer that renders to braille Unicode characters.

    Each terminal cell = 2 pixels wide x 4 pixels tall.
    """

    def __init__(self, term_cols, term_rows):
        self.term_cols = term_cols
        self.term_rows = term_rows
        self.pixel_width = term_cols * 2
        self.pixel_height = term_rows * 4
        self.buffer = np.zeros((term_rows, term_cols), dtype=np.uint8)

    def clear(self):
        self.buffer[:] = 0

    def set_pixel(self, x, y):
        if x < 0 or x >= self.pixel_width or y < 0 or y >= self.pixel_height:
            return
        col = x // 2
        row = y // 4
        self.buffer[row, col] |= BRAILLE_MAP[y % 4][x % 2]

    def render_to_curses(self, stdscr, offset_row=0, offset_col=0):
        for r in range(self.term_rows):
            line_parts = []
            for c in range(self.term_cols):
                b = self.buffer[r, c]
                line_parts.append(chr(BRAILLE_BASE | int(b)))
            line = ''.join(line_parts)
            try:
                stdscr.addstr(r + offset_row, offset_col, line)
            except curses.error:
                pass  # edge of screen


class Renderer:
    """Coordinates all terminal output: canvas, status, narration, borders."""

    # Layout: row 0 = top border, rows 1..H = canvas, row H+1 = bottom border,
    # row H+2 = status, row H+3 = narration
    BORDER_TOP = 0
    CANVAS_OFFSET = 1
    STATUS_LINES = 2  # status + narration

    def __init__(self, stdscr):
        self.stdscr = stdscr
        curses.curs_set(0)
        stdscr.nodelay(True)
        stdscr.timeout(33)  # ~30fps
        try:
            curses.start_color()
            curses.use_default_colors()
        except curses.error:
            pass

        self.mode = 'micro'
        self._calc_dimensions()

    def _calc_dimensions(self):
        self.term_rows, self.term_cols = self.stdscr.getmaxyx()
        # Reserve: 1 top border + 1 bottom border + 2 status lines
        canvas_term_rows = max(self.term_rows - 4, 1)
        canvas_term_cols = max(self.term_cols - 2, 1)  # 1 border each side
        self.canvas = BrailleCanvas(canvas_term_cols, canvas_term_rows)
        self.canvas_rows = canvas_term_rows
        self.canvas_cols = canvas_term_cols
        self.border_bottom_row = self.CANVAS_OFFSET + canvas_term_rows
        self.status_row = self.border_bottom_row + 1
        self.narration_row = self.status_row + 1

    def pixel_bounds(self):
        """Return (width, height) in braille pixels — use as physics bounds."""
        return self.canvas.pixel_width, self.canvas.pixel_height

    def handle_resize(self):
        self._calc_dimensions()
        self.stdscr.clear()

    def draw_micro(self, positions):
        """Plot each particle as a braille dot."""
        self.canvas.clear()
        for i in range(len(positions)):
            self.canvas.set_pixel(int(positions[i, 0]), int(positions[i, 1]))

    def draw_macro(self, cell_counts):
        """Render density heatmap using block characters."""
        rows, cols = cell_counts.shape
        max_count = cell_counts.max() if cell_counts.max() > 0 else 1

        # Map each cell to a region of the canvas terminal area
        for r in range(self.canvas_rows):
            line = []
            for c in range(self.canvas_cols):
                # Which physics cell does this terminal cell fall in?
                gr = min(int(r * rows / self.canvas_rows), rows - 1)
                gc = min(int(c * cols / self.canvas_cols), cols - 1)
                density = cell_counts[gr, gc] / max_count
                idx = min(int(density * (len(DENSITY_CHARS) - 1)), len(DENSITY_CHARS) - 1)
                line.append(DENSITY_CHARS[idx])
            try:
                self.stdscr.addstr(r + self.CANVAS_OFFSET, 1, ''.join(line))
            except curses.error:
                pass

    def draw_box_border(self):
        w = min(self.canvas_cols + 2, self.term_cols)
        try:
            # Top
            self.stdscr.addstr(self.BORDER_TOP, 0,
                               BOX_TL + BOX_H * (w - 2) + BOX_TR)
            # Sides
            for r in range(self.CANVAS_OFFSET, self.border_bottom_row):
                self.stdscr.addstr(r, 0, BOX_V)
                if w - 1 < self.term_cols:
                    self.stdscr.addstr(r, w - 1, BOX_V)
            # Bottom
            self.stdscr.addstr(self.border_bottom_row, 0,
                               BOX_BL + BOX_H * (w - 2) + BOX_BR)
        except curses.error:
            pass

    def draw_status(self, entropy, entropy_norm, temperature, n_particles,
                    time_dir, paused, step_count):
        arrow = '→' if time_dir == 1 else '←'
        pause_str = ' [PAUSED]' if paused else ''
        line = (f' S={entropy:.1f}  S/Smax={entropy_norm:.3f}  '
                f'T={temperature:.2f}  N={n_particles}  '
                f't{arrow}  step={step_count}{pause_str}')
        line = line[:self.term_cols - 1]
        try:
            self.stdscr.addstr(self.status_row, 0, line)
        except curses.error:
            pass

    def draw_narration(self, text):
        if not text:
            return
        text = text[:self.term_cols - 2]
        try:
            self.stdscr.addstr(self.narration_row, 1, text)
        except curses.error:
            pass

    def draw_help_overlay(self):
        """Minimal help overlay."""
        lines = [
            '╭─────────────────────────────╮',
            '│  ENTROPY — CONTROLS         │',
            '│                             │',
            '│  SPACE   pause / resume     │',
            '│  r       reverse time       │',
            '│  m       macro / micro view │',
            '│  +/-     add / remove parts │',
            '│  ?       toggle this help   │',
            '│  q       quit               │',
            '│                             │',
            '│  S = k_B ln Ω              │',
            '╰─────────────────────────────╯',
        ]
        start_r = max(0, (self.term_rows - len(lines)) // 2)
        start_c = max(0, (self.term_cols - len(lines[0])) // 2)
        for i, line in enumerate(lines):
            try:
                self.stdscr.addstr(start_r + i, start_c, line)
            except curses.error:
                pass

    def begin_frame(self):
        self.stdscr.erase()

    def end_frame(self):
        self.stdscr.refresh()
