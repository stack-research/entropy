"""Module 3: Maxwell's Demon.

The user becomes the demon, opening and closing a gate between two chambers
to sort fast and slow particles. Track the information cost of each decision.
Landauer's principle: the demon always loses."""

import curses
import numpy as np
from math import log
from core.engine import ParticleSystem, K_B
from core.renderer import BrailleCanvas, BRAILLE_BASE, BOX_TL, BOX_TR, BOX_BL, BOX_BR, BOX_H, BOX_V
from core.narrator import Narrator


def make_demon_narrator():
    n = Narrator()
    n.add_rule(
        lambda s: s.get('step', 0) == 1,
        'You are the demon. Open the gate to let fast particles right, slow ones left.',
        duration=200,
    )
    n.add_rule(
        lambda s: s.get('decisions', 0) >= 3,
        'Each decision you make requires information. Information has a thermodynamic cost.',
        duration=180,
    )
    n.add_rule(
        lambda s: s.get('decisions', 0) >= 10,
        'Landauer\'s principle: erasing one bit of information dissipates at least k_B T ln(2) of energy.',
        duration=200,
    )
    n.add_rule(
        lambda s: s.get('info_cost', 0) > s.get('entropy_reduced', 0) and s.get('decisions', 0) > 5,
        'The cost of your knowledge exceeds the entropy you\'ve reduced. The demon always loses.',
        duration=250,
    )
    n.add_rule(
        lambda s: s.get('decisions', 0) >= 25,
        'Your brain dissipates ~20 watts. Each neural computation is an irreversible erasure.',
        duration=200,
    )
    n.set_controls('SPACE open/close gate  p pause  r reset  q back')

    return n


class DemonSystem:
    """Two-chamber particle system with a gate the user controls."""

    def __init__(self, n_particles, bounds, temperature=1.0):
        self.n = n_particles
        self.width, self.height = bounds
        self.bounds = bounds
        self.dt = 1.0
        self.temperature = temperature
        self.gate_open = False
        self.gate_y_min = self.height * 0.35
        self.gate_y_max = self.height * 0.65
        self.wall_x = self.width // 2
        self.decisions = 0
        self.info_bits = 0.0  # information cost in bits

        # Initialize particles uniformly in left chamber
        sigma = np.sqrt(K_B * temperature)
        self.pos = np.column_stack([
            np.random.uniform(2, self.wall_x - 2, n_particles),
            np.random.uniform(2, self.height - 2, n_particles),
        ])
        self.vel = np.random.normal(0, sigma, (n_particles, 2))
        self.speeds = np.sqrt(self.vel[:, 0]**2 + self.vel[:, 1]**2)

    def toggle_gate(self):
        self.gate_open = not self.gate_open
        self.decisions += 1
        # Each gate operation = observing particles near gate = ~1 bit per particle near gate
        near_gate = np.sum(
            (np.abs(self.pos[:, 0] - self.wall_x) < 10) &
            (self.pos[:, 1] > self.gate_y_min) &
            (self.pos[:, 1] < self.gate_y_max)
        )
        self.info_bits += max(1.0, near_gate * 0.5)

    def step(self):
        self.pos += self.vel * self.dt
        self.speeds = np.sqrt(self.vel[:, 0]**2 + self.vel[:, 1]**2)
        self._reflect_walls()

    def _reflect_walls(self):
        # Outer walls
        for axis, limit in [(0, self.width), (1, self.height)]:
            lo = self.pos[:, axis] < 0
            self.pos[lo, axis] = -self.pos[lo, axis]
            self.vel[lo, axis] = -self.vel[lo, axis]

            hi = self.pos[:, axis] >= limit
            self.pos[hi, axis] = 2 * limit - self.pos[hi, axis]
            self.vel[hi, axis] = -self.vel[hi, axis]

        # Internal wall with gate
        for i in range(self.n):
            px, py = self.pos[i]
            # Check if particle is crossing the wall
            if abs(px - self.wall_x) < abs(self.vel[i, 0] * self.dt) + 1:
                in_gate = self.gate_y_min <= py <= self.gate_y_max
                if not (self.gate_open and in_gate):
                    # Reflect off internal wall
                    if self.vel[i, 0] > 0 and px >= self.wall_x and px < self.wall_x + 3:
                        self.pos[i, 0] = 2 * self.wall_x - px
                        self.vel[i, 0] = -self.vel[i, 0]
                    elif self.vel[i, 0] < 0 and px <= self.wall_x and px > self.wall_x - 3:
                        self.pos[i, 0] = 2 * self.wall_x - px
                        self.vel[i, 0] = -self.vel[i, 0]

    def chamber_stats(self):
        """Return (left_count, right_count, left_avg_speed, right_avg_speed)."""
        left = self.pos[:, 0] < self.wall_x
        right = ~left
        n_left = np.sum(left)
        n_right = np.sum(right)
        avg_left = np.mean(self.speeds[left]) if n_left > 0 else 0
        avg_right = np.mean(self.speeds[right]) if n_right > 0 else 0
        return int(n_left), int(n_right), float(avg_left), float(avg_right)

    def entropy_reduced(self):
        """Estimate entropy reduction from sorting (in natural units)."""
        n_left, n_right, avg_l, avg_r = self.chamber_stats()
        if n_left == 0 or n_right == 0:
            return 0.0
        # Temperature difference as proxy for sorting quality
        t_diff = abs(avg_l - avg_r)
        avg_speed = np.mean(self.speeds)
        if avg_speed < 1e-6:
            return 0.0
        return K_B * self.n * (t_diff / avg_speed)

    def info_cost_entropy(self):
        """Convert information cost (bits) to entropy units."""
        return self.info_bits * K_B * log(2)


def run(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(33)
    try:
        curses.start_color()
        curses.use_default_colors()
    except curses.error:
        pass

    narrator = make_demon_narrator()

    def setup():
        rows, cols = stdscr.getmaxyx()
        canvas_cols = max(cols - 2, 4)
        canvas_rows = max(rows - 5, 1)
        pw = canvas_cols * 2
        ph = canvas_rows * 4
        return DemonSystem(120, (pw, ph)), BrailleCanvas(canvas_cols, canvas_rows), canvas_rows, canvas_cols

    system, canvas, canvas_rows, canvas_cols = setup()
    step_count = 0
    paused = False

    while True:
        key = stdscr.getch()

        if key == ord('q'):
            break
        elif key == ord(' '):
            system.toggle_gate()
        elif key == ord('p'):
            paused = not paused
        elif key == ord('r'):
            system, canvas, canvas_rows, canvas_cols = setup()
            step_count = 0
            narrator = make_demon_narrator()
        elif key == curses.KEY_RESIZE:
            system, canvas, canvas_rows, canvas_cols = setup()
            step_count = 0
            stdscr.clear()

        if not paused:
            system.step()
            step_count += 1

        n_left, n_right, avg_l, avg_r = system.chamber_stats()
        entropy_reduced = system.entropy_reduced()
        info_cost = system.info_cost_entropy()

        narrator.update({
            'step': step_count,
            'decisions': system.decisions,
            'info_cost': info_cost,
            'entropy_reduced': entropy_reduced,
        })

        # --- Render ---
        stdscr.erase()
        rows, cols = stdscr.getmaxyx()

        # Border
        w = min(canvas_cols + 2, cols)
        try:
            stdscr.addstr(0, 0, BOX_TL + BOX_H * (w - 2) + BOX_TR)
            for r in range(1, canvas_rows + 1):
                stdscr.addstr(r, 0, BOX_V)
                if w - 1 < cols:
                    stdscr.addstr(r, w - 1, BOX_V)
            stdscr.addstr(canvas_rows + 1, 0, BOX_BL + BOX_H * (w - 2) + BOX_BR)
        except curses.error:
            pass

        # Particles on canvas
        canvas.clear()
        median_speed = np.median(system.speeds) if system.n > 0 else 1.0
        positions = system.pos.astype(int)
        for i in range(system.n):
            x = max(0, min(int(positions[i, 0]), canvas.pixel_width - 1))
            y = max(0, min(int(positions[i, 1]), canvas.pixel_height - 1))
            canvas.set_pixel(x, y)

        canvas.render_to_curses(stdscr, 1, 1)

        # Draw internal wall
        wall_col = system.wall_x // 2  # convert pixel to terminal col
        gate_row_min = int(system.gate_y_min) // 4
        gate_row_max = int(system.gate_y_max) // 4
        for r in range(canvas_rows):
            if system.gate_open and gate_row_min <= r <= gate_row_max:
                ch = ' ' if system.gate_open else BOX_V
            else:
                ch = BOX_V
            try:
                stdscr.addstr(r + 1, wall_col + 1, ch)
            except curses.error:
                pass

        # Gate indicator
        gate_str = "[GATE OPEN]" if system.gate_open else "[GATE CLOSED]"

        # Status
        status_row = min(canvas_rows + 2, rows - 2)
        status = (f' L: n={n_left} v\u0305={avg_l:.2f}  R: n={n_right} v\u0305={avg_r:.2f}  '
                  f'{gate_str}  decisions={system.decisions}')
        try:
            stdscr.addstr(status_row, 0, status[:cols - 1])
        except curses.error:
            pass

        # Entropy accounting
        acct_row = min(status_row + 1, rows - 1)
        acct = f' \u0394S_reduced={entropy_reduced:.2f}  info_cost={info_cost:.2f}  net={entropy_reduced - info_cost:.2f}'
        try:
            stdscr.addstr(acct_row, 0, acct[:cols - 1])
        except curses.error:
            pass

        # Narration
        narr = narrator.current_text()
        if narr:
            narr_row = min(acct_row + 1, rows - 1)
            try:
                stdscr.addstr(narr_row, 1, narr[:cols - 2])
            except curses.error:
                pass

        stdscr.refresh()
