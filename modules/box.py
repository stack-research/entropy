"""Module 1: The Box.

A particle grid simulation where you watch an ordered system dissolve
into equilibrium. Run it backward and watch the absurdity."""

import curses
from core.engine import ParticleSystem
from core.renderer import Renderer
from core.narrator import make_box_narrator
from core.terminal import require_terminal_size


def run(stdscr):
    renderer = Renderer(stdscr)
    pw, ph = renderer.pixel_bounds()

    system = ParticleSystem(
        n_particles=200,
        bounds=(pw, ph),
        initial_config='corner',
        temperature=1.0,
    )

    narrator = make_box_narrator()

    paused = False
    show_help = False
    step_count = 0
    first_pause_sent = False
    just_reversed = False
    entropy_calc_interval = 3  # recalc every N frames
    cached_entropy = 0.0
    cached_entropy_norm = 0.0
    cached_cell_counts = None

    while True:
        size_state = require_terminal_size(stdscr)
        if size_state == 'quit':
            break
        if size_state != 'ok':
            continue

        # --- Input ---
        key = stdscr.getch()
        just_reversed = False

        if key == ord('q'):
            break
        elif key == ord(' '):
            paused = not paused
            if paused and not first_pause_sent:
                first_pause_sent = True
        elif key == ord('r'):
            system.reverse()
            just_reversed = True
        elif key == ord('m'):
            renderer.mode = 'macro' if renderer.mode == 'micro' else 'micro'
        elif key in (ord('+'), ord('=')):
            system.add_particles(10)
        elif key == ord('-'):
            system.remove_particles(10)
        elif key == ord('?'):
            show_help = not show_help
        elif key == curses.KEY_RESIZE:
            renderer.handle_resize()
            pw, ph = renderer.pixel_bounds()
            # Rescale positions to new bounds
            if system.width > 0 and system.height > 0:
                system.pos[:, 0] *= pw / system.width
                system.pos[:, 1] *= ph / system.height
            system.width, system.height = pw, ph
            system.bounds = (pw, ph)

        # --- Step ---
        if not paused:
            system.step()
            step_count += 1

        # --- Entropy (throttled) ---
        if step_count % entropy_calc_interval == 0 or cached_cell_counts is None:
            cached_entropy, cached_cell_counts = system.entropy()
            s_max = system.entropy_max()
            cached_entropy_norm = min(cached_entropy / s_max, 1.0) if s_max > 0 else 0.0

        # --- Narrator ---
        narrator.update({
            'entropy_norm': cached_entropy_norm,
            'time_dir': system.time_direction,
            'just_reversed': just_reversed,
            'first_pause': first_pause_sent and paused,
            'step': step_count,
        })

        # --- Render ---
        renderer.begin_frame()
        renderer.draw_box_border()

        if renderer.mode == 'micro':
            positions = system.particle_positions()
            renderer.draw_micro(positions)
            renderer.canvas.render_to_curses(stdscr, renderer.CANVAS_OFFSET, 1)
        else:
            renderer.draw_macro(cached_cell_counts)

        renderer.draw_status(
            cached_entropy, cached_entropy_norm,
            system.measured_temperature(), system.n,
            system.time_direction, paused, step_count,
        )
        renderer.draw_narration(narrator.current_text())

        if show_help:
            renderer.draw_help_overlay()

        renderer.end_frame()
