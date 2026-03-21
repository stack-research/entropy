"""Module 6: Self-Entropy.

The simulation measures its own thermodynamic cost. CPU usage, memory,
the Landauer bound on computation. The observer cannot escape the observation."""

import curses
import time
import os
import sys
from math import log
from core.constants import K_B_SI, T_ROOM
from core.narrator import Narrator
from core.terminal import require_terminal_size

LANDAUER_LIMIT = K_B_SI * T_ROOM * log(2)  # ~2.85e-21 J per bit erased


def make_self_narrator():
    n = Narrator()
    n.add_rule(
        lambda s: s.get('step', 0) == 1,
        'This simulation is a thermodynamic process. It dissipates energy. It increases entropy.',
        duration=200,
    )
    n.add_rule(
        lambda s: s.get('step', 0) > 100,
        f'Landauer limit: erasing one bit costs at least {LANDAUER_LIMIT:.2e} J at room temperature.',
        duration=200,
    )
    n.add_rule(
        lambda s: s.get('step', 0) > 250,
        'Your CPU dissipates ~10 billion times the Landauer limit per operation. We are wasteful machines.',
        duration=200,
    )
    n.add_rule(
        lambda s: s.get('step', 0) > 500,
        'The total entropy of the universe increased because you ran this program.',
        duration=200,
    )
    n.add_rule(
        lambda s: s.get('step', 0) > 800,
        'Every measurement, every computation, every thought — irreversible. The observer pays.',
        duration=250,
    )
    n.set_controls('q back')

    return n


def get_cpu_times():
    """Get cumulative CPU times for this process."""
    try:
        times = os.times()
        return times.user + times.system
    except Exception:
        return 0.0


def estimate_operations(cpu_seconds, ghz=3.0):
    """Rough estimate of CPU operations from CPU time."""
    return int(cpu_seconds * ghz * 1e9)


def normalize_rss_bytes(raw_rss, platform):
    """Normalize ru_maxrss to bytes across macOS and Linux."""
    if raw_rss <= 0:
        return 0
    if platform == 'darwin':
        return int(raw_rss)
    return int(raw_rss * 1024)


def get_memory_bytes():
    """Get resident memory of this process."""
    try:
        import resource
        usage = resource.getrusage(resource.RUSAGE_SELF)
        return normalize_rss_bytes(usage.ru_maxrss, sys.platform)
    except Exception:
        return 0


def run(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(100)
    try:
        curses.start_color()
        curses.use_default_colors()
    except curses.error:
        pass

    narrator = make_self_narrator()
    start_time = time.monotonic()
    start_cpu = get_cpu_times()
    tick = 0
    total_bits_erased = 0

    # Simulated "computation" — we generate random bits and erase them
    # to demonstrate Landauer's principle concretely
    import numpy as np
    rng_state = np.random.RandomState(42)

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
            stdscr.clear()

        tick += 1
        rows, cols = stdscr.getmaxyx()

        # Do actual computation to measure
        rng_state.randint(0, 256, size=1000, dtype=np.uint8)
        bits_this_tick = 8000  # 1000 bytes = 8000 bits
        total_bits_erased += bits_this_tick

        elapsed = time.monotonic() - start_time
        cpu_used = get_cpu_times() - start_cpu
        ops = estimate_operations(cpu_used)
        mem = get_memory_bytes()

        # Thermodynamic accounting
        landauer_min_energy = total_bits_erased * LANDAUER_LIMIT
        # Real CPU: ~1e-10 J per operation (modern CPU at ~50W, ~5e11 ops/sec)
        real_energy_per_op = 1e-10
        estimated_real_energy = ops * real_energy_per_op
        entropy_produced = estimated_real_energy / T_ROOM  # dS = dQ/T
        landauer_entropy = landauer_min_energy / T_ROOM

        narrator.update({'step': tick})

        # --- Render ---
        stdscr.erase()

        title = "SELF-ENTROPY: THE COST OF OBSERVATION"
        c = max(0, (cols - len(title)) // 2)
        try:
            stdscr.addstr(0, c, title, curses.A_BOLD)
        except curses.error:
            pass

        # Divider
        try:
            stdscr.addstr(1, 0, '\u2500' * min(cols - 1, 60))
        except curses.error:
            pass

        lines = [
            ('PROCESS METRICS', True),
            (f'  Elapsed time:       {elapsed:.1f} s', False),
            (f'  CPU time:           {cpu_used:.3f} s', False),
            (f'  Est. operations:    {ops:,}', False),
            (f'  Memory (RSS):       {mem:,} bytes', False),
            ('', False),
            ('INFORMATION', True),
            (f'  Bits generated:     {total_bits_erased:,}', False),
            (f'  Bits per second:    {total_bits_erased / max(elapsed, 0.01):,.0f}', False),
            ('', False),
            ('THERMODYNAMIC COST', True),
            (f'  Landauer minimum:   {landauer_min_energy:.2e} J', False),
            (f'  Est. actual energy: {estimated_real_energy:.2e} J', False),
            (f'  Waste factor:       {estimated_real_energy / max(landauer_min_energy, 1e-30):.0f}x Landauer limit', False),
            ('', False),
            ('ENTROPY PRODUCED', True),
            (f'  Landauer bound:     {landauer_entropy:.2e} J/K', False),
            (f'  Estimated actual:   {entropy_produced:.2e} J/K', False),
            (f'  \u0394S universe:        +{entropy_produced:.2e} J/K', False),
        ]

        for i, (line, is_header) in enumerate(lines):
            r = i + 3
            if r >= rows - 2:
                break
            try:
                if is_header:
                    stdscr.addstr(r, 1, line[:cols - 2], curses.A_BOLD)
                else:
                    stdscr.addstr(r, 1, line[:cols - 2])
            except curses.error:
                pass

        # Live entropy bar
        bar_row = min(3 + len(lines) + 1, rows - 3)
        bar_width = min(50, cols - 10)
        if bar_width > 5 and bar_row < rows - 2:
            # Scale: log of entropy produced
            if entropy_produced > 0:
                log_s = min(log(entropy_produced + 1e-30) / log(1e-10) * bar_width, bar_width)
                filled = max(0, int(log_s))
            else:
                filled = 0
            bar = '\u2588' * filled + '\u2591' * (bar_width - filled)
            try:
                stdscr.addstr(bar_row, 1, f' \u0394S [{bar}]')
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
