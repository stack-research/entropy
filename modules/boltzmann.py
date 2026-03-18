"""Module 5: Boltzmann Brain.

After heat death, the simulation keeps running. At absurd timescales,
a thermal fluctuation produces a momentary structure in the noise.
Was it conscious? The simulation doesn't answer."""

import curses
import random
import math
import time
from core.narrator import Narrator
from core.terminal import require_terminal_size

# The "brain" — a fleeting pattern that appears in noise
BRAIN_PATTERN = [
    "      .  .      ",
    "    .:::::::.   ",
    "  .::::::::::.  ",
    " .::::::::::::. ",
    " :::::::::::::::",
    " :::::::::::::::",
    " ':::::::::::::' ",
    "  ':::::::::::'  ",
    "    '::::::::'   ",
    "      ':::'      ",
]

FLUCTUATION_CHARS = [' ', ' ', ' ', ' ', '.', '\u00b7', '\u2219']


def make_boltzmann_narrator():
    n = Narrator()
    n.add_rule(
        lambda s: s.get('step', 0) == 1,
        'Heat death. Maximum entropy. Nothing happens. For a very long time.',
        duration=200,
    )
    n.add_rule(
        lambda s: s.get('log_year', 0) > 200,
        'Quantum fluctuations in the void. Mostly nothing.',
        duration=180,
    )
    n.add_rule(
        lambda s: s.get('log_year', 0) > 500,
        'Given enough time, any configuration of matter is possible. Including you.',
        duration=200,
    )
    n.add_rule(
        lambda s: s.get('approaching_brain', False),
        'A fluctuation. Structure emerging from thermal noise.',
        duration=150,
    )
    n.add_rule(
        lambda s: s.get('brain_visible', False),
        'A Boltzmann brain. A momentary observer in infinite emptiness. Was it conscious?',
        duration=300,
    )
    n.add_rule(
        lambda s: s.get('brain_faded', False),
        'The fluctuation dissipates. Equilibrium resumes. It changes nothing.',
        duration=250,
    )

    n.set_controls('q back')

    return n


def run(stdscr):
    curses.curs_set(1)  # blinking cursor in the void
    stdscr.nodelay(True)
    stdscr.timeout(150)
    try:
        curses.start_color()
        curses.use_default_colors()
    except curses.error:
        pass

    rows, cols = stdscr.getmaxyx()
    narrator = make_boltzmann_narrator()

    tick = 0
    log_year = 100.0  # start after heat death
    phase = 'waiting'  # waiting -> approaching -> brain -> fading -> post
    brain_tick = random.randint(400, 700)  # when the brain appears
    brain_duration = 120
    brain_start = 0
    approach_start = 0

    while True:
        size_state = require_terminal_size(stdscr)
        if size_state == 'quit':
            break
        if size_state != 'ok':
            continue

        key = stdscr.getch()
        if key == ord('q'):
            break
        elif key == curses.KEY_RESIZE:
            rows, cols = stdscr.getmaxyx()
            stdscr.clear()

        tick += 1
        log_year = 100 + tick * 1.5  # accelerating timescale

        # Phase transitions
        if phase == 'waiting' and tick >= brain_tick - 80:
            phase = 'approaching'
            approach_start = tick
        elif phase == 'approaching' and tick >= brain_tick:
            phase = 'brain'
            brain_start = tick
            curses.curs_set(0)
        elif phase == 'brain' and tick >= brain_start + brain_duration:
            phase = 'fading'
        elif phase == 'fading' and tick >= brain_start + brain_duration + 100:
            phase = 'post'
            curses.curs_set(1)

        narrator.update({
            'step': tick,
            'log_year': log_year,
            'approaching_brain': phase == 'approaching',
            'brain_visible': phase == 'brain',
            'brain_faded': phase == 'post',
        })

        # --- Render ---
        stdscr.erase()

        # Sparse random noise (thermal fluctuations)
        noise_density = 0.001
        if phase == 'approaching':
            # Noise increases as fluctuation builds
            progress = (tick - approach_start) / 80.0
            noise_density = 0.001 + progress * 0.015
        elif phase == 'fading':
            fade_progress = (tick - brain_start - brain_duration) / 100.0
            noise_density = 0.015 * (1 - fade_progress)

        for r in range(1, rows - 2):
            for c in range(cols - 1):
                if random.random() < noise_density:
                    ch = random.choice(FLUCTUATION_CHARS)
                    try:
                        stdscr.addstr(r, c, ch)
                    except curses.error:
                        pass

        # The brain itself
        if phase == 'brain':
            age = tick - brain_start
            visibility = min(1.0, age / 30.0)  # fade in
            if age > brain_duration - 40:
                visibility = max(0.0, (brain_duration - age) / 40.0)  # fade out

            br = max(0, (rows - len(BRAIN_PATTERN)) // 2)
            bc = max(0, (cols - len(BRAIN_PATTERN[0])) // 2)
            for i, line in enumerate(BRAIN_PATTERN):
                for j, ch in enumerate(line):
                    if ch != ' ' and random.random() < visibility:
                        try:
                            stdscr.addstr(br + i, bc + j, ch,
                                          curses.A_BOLD if visibility > 0.7 else 0)
                        except curses.error:
                            pass

        # Timescale counter
        time_str = f' 10^{log_year:.0f} years'
        try:
            stdscr.addstr(rows - 2, 0, time_str[:cols - 1], curses.A_DIM)
        except curses.error:
            pass

        # Narration
        narr = narrator.current_text()
        if narr:
            try:
                stdscr.addstr(rows - 1, 1, narr[:cols - 2])
            except curses.error:
                pass

        stdscr.refresh()

        # After post-brain, just sit in the void
        if phase == 'post' and tick > brain_start + brain_duration + 300:
            stdscr.erase()
            stdscr.refresh()
            stdscr.timeout(-1)
            while True:
                k = stdscr.getch()
                if k == ord('q'):
                    return
            break
