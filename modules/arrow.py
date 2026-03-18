"""Module 2: The Arrow of Time.

Two simulations side by side. One runs forward from low entropy,
one runs backward from high entropy. At low entropy differences,
you genuinely cannot tell which is 'real.' As the gradient increases,
the arrow becomes obvious."""

import curses
import numpy as np
from core.engine import ParticleSystem
from core.renderer import BrailleCanvas, BOX_V
from core.narrator import Narrator

BACKWARD_PREP_STEPS = 240
BACKWARD_TARGET_ENTROPY = 0.75


def make_arrow_narrator():
    n = Narrator()
    n.add_rule(
        lambda s: s.get('step', 0) == 1,
        'Two systems. One moves forward in time. One moves backward. Which is which?',
        duration=180,
    )
    n.add_rule(
        lambda s: s.get('step', 0) > 60 and abs(s.get('entropy_diff', 0)) < 0.1,
        'At equilibrium, the arrow of time vanishes. Past and future become indistinguishable.',
        duration=180,
    )
    n.add_rule(
        lambda s: s.get('revealed', False),
        'We remember the past because it had lower entropy. Memory requires a gradient.',
        duration=200,
    )
    n.add_rule(
        lambda s: s.get('step', 0) > 300 and not s.get('revealed', False),
        'Press SPACE to reveal which is forward. Press r to reset with a new arrangement.',
        duration=200,
    )
    n.set_controls('SPACE reveal  r reset  q back')

    return n


def build_arrow_systems(bounds, n_particles=150):
    """Create one forward system and one genuinely time-reversed system."""
    sys_forward = ParticleSystem(n_particles, bounds, 'corner', temperature=1.0)
    sys_backward = ParticleSystem(n_particles, bounds, 'corner', temperature=1.0)

    for _ in range(BACKWARD_PREP_STEPS):
        sys_backward.step()

    extra_steps = 0
    while sys_backward.entropy_normalized() < BACKWARD_TARGET_ENTROPY and extra_steps < 240:
        sys_backward.step()
        extra_steps += 1

    sys_backward.reverse()
    return sys_forward, sys_backward


def run(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(33)
    try:
        curses.start_color()
        curses.use_default_colors()
    except curses.error:
        pass

    rows, cols = stdscr.getmaxyx()
    narrator = make_arrow_narrator()

    def setup():
        nonlocal rows, cols
        rows, cols = stdscr.getmaxyx()
        half_cols = max((cols - 3) // 2, 4)
        canvas_rows = max(rows - 5, 1)
        pw = half_cols * 2
        ph = canvas_rows * 4

        sys_a, sys_b = build_arrow_systems((pw, ph))

        canvas_a = BrailleCanvas(half_cols, canvas_rows)
        canvas_b = BrailleCanvas(half_cols, canvas_rows)

        # Randomly assign left/right so user can't just guess
        if np.random.random() < 0.5:
            return sys_a, sys_b, canvas_a, canvas_b, half_cols, canvas_rows, pw, ph, False
        else:
            return sys_b, sys_a, canvas_b, canvas_a, half_cols, canvas_rows, pw, ph, True

    sys_left, sys_right, canvas_l, canvas_r, half_cols, canvas_rows, pw, ph, swapped = setup()
    step_count = 0
    paused = False
    revealed = False

    while True:
        key = stdscr.getch()

        if key == ord('q'):
            break
        elif key == ord(' '):
            if not revealed:
                revealed = True
            else:
                paused = not paused
        elif key == ord('r'):
            sys_left, sys_right, canvas_l, canvas_r, half_cols, canvas_rows, pw, ph, swapped = setup()
            step_count = 0
            revealed = False
            paused = False
            narrator = make_arrow_narrator()
        elif key == curses.KEY_RESIZE:
            sys_left, sys_right, canvas_l, canvas_r, half_cols, canvas_rows, pw, ph, swapped = setup()
            step_count = 0
            stdscr.clear()

        if not paused:
            sys_left.step()
            sys_right.step()
            step_count += 1

        # Entropy
        e_left_norm = sys_left.entropy_normalized()
        e_right_norm = sys_right.entropy_normalized()

        narrator.update({
            'step': step_count,
            'entropy_diff': e_left_norm - e_right_norm,
            'revealed': revealed,
        })

        # --- Render ---
        stdscr.erase()
        rows, cols = stdscr.getmaxyx()
        right_offset = half_cols + 3

        # Labels
        if revealed:
            if swapped:
                left_label = " HIGHER ENTROPY (backward)"
                right_label = " LOW ENTROPY (forward)"
            else:
                left_label = " LOW ENTROPY (forward)"
                right_label = " HIGHER ENTROPY (backward)"
        else:
            left_label = " SYSTEM A"
            right_label = " SYSTEM B"

        try:
            stdscr.addstr(0, 1, left_label[:half_cols], curses.A_BOLD)
            stdscr.addstr(0, right_offset, right_label[:half_cols], curses.A_BOLD)
        except curses.error:
            pass

        # Draw canvases
        canvas_l.clear()
        canvas_r.clear()
        pos_l = sys_left.particle_positions()
        pos_r = sys_right.particle_positions()
        for i in range(len(pos_l)):
            canvas_l.set_pixel(int(pos_l[i, 0]), int(pos_l[i, 1]))
        for i in range(len(pos_r)):
            canvas_r.set_pixel(int(pos_r[i, 0]), int(pos_r[i, 1]))

        canvas_l.render_to_curses(stdscr, 1, 1)
        canvas_r.render_to_curses(stdscr, 1, right_offset)

        # Divider
        for r in range(1, min(canvas_rows + 1, rows - 3)):
            try:
                stdscr.addstr(r, half_cols + 1, BOX_V)
            except curses.error:
                pass

        # Status
        status_row = min(canvas_rows + 2, rows - 2)
        status = f' S/Smax: L={e_left_norm:.3f}  R={e_right_norm:.3f}  step={step_count}'
        if paused:
            status += '  [PAUSED]'
        try:
            stdscr.addstr(status_row, 0, status[:cols - 1])
        except curses.error:
            pass

        # Narration
        narr = narrator.current_text()
        if narr:
            try:
                stdscr.addstr(min(status_row + 1, rows - 1), 1, narr[:cols - 2])
            except curses.error:
                pass

        stdscr.refresh()
