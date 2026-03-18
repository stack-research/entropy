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
from core.terminal import require_terminal_size


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
    """Two-chamber particle system with a gate the user controls.

    Built on ParticleSystem with elastic collisions enabled so particles
    exchange energy. The demon's job is to sort fast particles into the
    right chamber and slow ones into the left — fighting thermalization.
    """

    def __init__(self, n_particles, bounds, temperature=1.0):
        self.n = n_particles
        self.width, self.height = bounds
        self.bounds = bounds
        self.temperature = temperature
        self.gate_open = False
        self.gate_y_min = self.height * 0.35
        self.gate_y_max = self.height * 0.65
        self.wall_x = self.width // 2

        # Tracking
        self.decisions = 0
        self.info_bits = 0.0
        self.initial_entropy = None

        # Use the real engine with collisions
        self.system = ParticleSystem(
            n_particles, bounds,
            initial_config='half',
            temperature=temperature,
            collisions=True,
            collision_radius=3.0,
        )
        # Confine to left chamber initially
        self.system.pos[:, 0] = np.random.uniform(2, self.wall_x - 2, n_particles)

    @property
    def pos(self):
        return self.system.pos

    @property
    def vel(self):
        return self.system.vel

    @property
    def speeds(self):
        return np.sqrt(self.vel[:, 0]**2 + self.vel[:, 1]**2)

    def toggle_gate(self):
        self.gate_open = not self.gate_open
        self.decisions += 1

        # Information cost: to decide whether to open/close, the demon
        # must observe each particle near the gate. Each observation is
        # at least 1 bit (fast or slow?). This is the measurement that
        # Landauer's principle taxes.
        near_gate = np.sum(
            (np.abs(self.pos[:, 0] - self.wall_x) < 15) &
            (self.pos[:, 1] > self.gate_y_min) &
            (self.pos[:, 1] < self.gate_y_max)
        )
        # 1 bit per particle observed (binary classification: fast/slow)
        self.info_bits += max(1.0, float(near_gate))

    def step(self):
        prev_pos = self.system.pos.copy()
        # Step the underlying physics (with collisions)
        self.system.step()
        # Enforce the internal wall
        self._enforce_wall(prev_pos)
        # Snapshot initial entropy on first step
        if self.initial_entropy is None:
            self.initial_entropy = self._two_chamber_entropy()

    def _enforce_wall(self, prev_pos):
        """Reflect particles off the internal dividing wall, with gate.

        Reflection is based on whether a particle crossed the wall during the
        timestep, so fast particles cannot tunnel through a closed gate.
        """
        pos = self.system.pos
        vel = self.system.vel
        wx = self.wall_x

        for i in range(self.n):
            prev_x, prev_y = prev_pos[i]
            px, py = pos[i]
            dx = px - prev_x
            if abs(dx) < 1e-10:
                continue

            crossed = ((prev_x < wx <= px) or (prev_x > wx >= px))
            if not crossed:
                continue

            t_cross = (wx - prev_x) / dx
            cross_y = prev_y + (py - prev_y) * t_cross
            in_gate = self.gate_y_min <= cross_y <= self.gate_y_max
            if self.gate_open and in_gate:
                continue  # pass through

            pos[i, 0] = 2 * wx - px
            vel[i, 0] = -vel[i, 0]

    def chamber_stats(self):
        """Return (left_count, right_count, left_temp, right_temp).

        Temperature from equipartition: T = <mv^2> / (d * k_B), d=2, m=1.
        Using temperature (not avg speed) because that's what the demon
        is actually sorting — kinetic energy, not speed.
        """
        left_mask = self.pos[:, 0] < self.wall_x
        right_mask = ~left_mask
        n_left = int(np.sum(left_mask))
        n_right = int(np.sum(right_mask))

        # T = mean(v^2) / 2 for 2D, m=1, k_B=1
        if n_left > 0:
            t_left = float(np.mean(self.vel[left_mask] ** 2))
        else:
            t_left = 0.0

        if n_right > 0:
            t_right = float(np.mean(self.vel[right_mask] ** 2))
        else:
            t_right = 0.0

        return n_left, n_right, t_left, t_right

    def _two_chamber_entropy(self):
        """Entropy of the two-chamber system.

        S = S_config + S_thermal
        S_config: Boltzmann counting of left/right particle distribution
        S_thermal: sum of per-chamber thermal entropy from KE distribution
        """
        left_mask = self.pos[:, 0] < self.wall_x
        n_left = int(np.sum(left_mask))
        n_right = self.n - n_left

        # Configurational: S_config = k_B * ln(N! / (n_L! * n_R!))
        from math import lgamma
        s_config = K_B * (lgamma(self.n + 1)
                          - lgamma(n_left + 1) - lgamma(n_right + 1))

        # Thermal: for an ideal gas, S_thermal ~ N * k_B * ln(T) (up to constant)
        # We track the *change* from initial state, so the constant cancels
        speeds_sq = self.vel[:, 0]**2 + self.vel[:, 1]**2
        if n_left > 0:
            t_left = float(np.mean(speeds_sq[left_mask]))
        else:
            t_left = 1.0
        if n_right > 0:
            t_right = float(np.mean(speeds_sq[~left_mask]))
        else:
            t_right = 1.0

        s_thermal = 0.0
        if n_left > 0 and t_left > 0:
            s_thermal += n_left * K_B * log(t_left)
        if n_right > 0 and t_right > 0:
            s_thermal += n_right * K_B * log(t_right)

        return s_config + s_thermal

    def entropy_reduced(self):
        """How much entropy has the demon reduced from the initial state?

        Positive = demon has succeeded in creating order.
        """
        if self.initial_entropy is None:
            return 0.0
        current = self._two_chamber_entropy()
        return max(0.0, self.initial_entropy - current)

    def info_cost_entropy(self):
        """Landauer cost: each bit erased costs at least k_B * ln(2).

        The demon must erase its memory after each measurement to make
        room for the next one. This is where the second law strikes back.
        """
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
        canvas_rows = max(rows - 6, 1)
        pw = canvas_cols * 2
        ph = canvas_rows * 4
        return DemonSystem(120, (pw, ph)), BrailleCanvas(canvas_cols, canvas_rows), canvas_rows, canvas_cols

    system, canvas, canvas_rows, canvas_cols = setup()
    step_count = 0
    paused = False

    while True:
        size_state = require_terminal_size(stdscr)
        if size_state == 'quit':
            break
        if size_state != 'ok':
            continue

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

        n_left, n_right, t_left, t_right = system.chamber_stats()
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
        positions = system.pos.astype(int)
        for i in range(system.n):
            x = max(0, min(int(positions[i, 0]), canvas.pixel_width - 1))
            y = max(0, min(int(positions[i, 1]), canvas.pixel_height - 1))
            canvas.set_pixel(x, y)

        canvas.render_to_curses(stdscr, 1, 1)

        # Draw internal wall
        wall_col = system.wall_x // 2
        gate_row_min = int(system.gate_y_min) // 4
        gate_row_max = int(system.gate_y_max) // 4
        for r in range(canvas_rows):
            if system.gate_open and gate_row_min <= r <= gate_row_max:
                ch = ' '
            else:
                ch = BOX_V
            try:
                stdscr.addstr(r + 1, wall_col + 1, ch)
            except curses.error:
                pass

        # Gate indicator
        gate_str = "[GATE OPEN]" if system.gate_open else "[GATE CLOSED]"

        # Status
        status_row = min(canvas_rows + 2, rows - 3)
        status = (f' L: n={n_left} T={t_left:.2f}  R: n={n_right} T={t_right:.2f}  '
                  f'{gate_str}  decisions={system.decisions}')
        try:
            stdscr.addstr(status_row, 0, status[:cols - 1])
        except curses.error:
            pass

        # Entropy accounting
        acct_row = min(status_row + 1, rows - 2)
        net = entropy_reduced - info_cost
        acct = (f' \u0394S_reduced={entropy_reduced:.2f}  '
                f'info_cost={info_cost:.2f} ({system.info_bits:.0f} bits)  '
                f'net={net:+.2f}')
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
