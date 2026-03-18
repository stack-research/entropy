"""Module 4: Heat Death Terminal.

Cosmological timescales compressed into ~5 minutes. Stars form, burn, die.
Black holes evaporate. The last photons red-shift into nothing.
The terminal slowly dims. Text gets sparser. Eventually — nothing.
Just a cursor blinking in void."""

import curses
import random
import math
import time
from core.narrator import Narrator

# Cosmological eras with approximate log-year timestamps
ERAS = [
    (0,     'STELLIFEROUS ERA',    'Stars burn. Galaxies collide. Light fills the void.'),
    (14,    'DEGENERATE ERA',      'The last stars gutter out. White dwarfs cool in darkness.'),
    (25,    'BLACK HOLE ERA',      'Only black holes remain, slowly evaporating via Hawking radiation.'),
    (40,    'DARK ERA',            'The black holes are gone. Photons red-shift toward zero.'),
    (60,    'ASYMPTOTIC SILENCE',  'Particles drift apart. No structure. No interaction. No time.'),
    (100,   'HEAT DEATH',          ''),
]

# Characters that represent matter at various densities
STAR_CHARS = ['*', '+', '.', '\u00b7', '\u2219', '\u2022', '\u25e6', '\u2726', '\u2727', '\u2729']
DIM_CHARS = ['\u2591', '\u2592', '\u2593', '\u2588']


def make_heatdeath_narrator():
    n = Narrator()
    n.add_rule(
        lambda s: s.get('era', 0) == 0 and s.get('step', 0) > 10,
        'Ten billion years per second. The sun is already gone.',
        duration=150,
    )
    n.add_rule(
        lambda s: s.get('era', 0) == 1,
        'Stellar nucleosynthesis ends. No new atoms will be forged.',
        duration=180,
    )
    n.add_rule(
        lambda s: s.get('era', 0) == 2,
        'Black holes: the last engines of entropy. They, too, are temporary.',
        duration=180,
    )
    n.add_rule(
        lambda s: s.get('era', 0) == 3,
        'The photon wavelength exceeds the observable universe. Light forgets itself.',
        duration=200,
    )
    n.add_rule(
        lambda s: s.get('era', 0) == 4,
        'Maximum entropy. Thermal equilibrium. The arrow of time dissolves.',
        duration=250,
    )
    n.add_rule(
        lambda s: s.get('era', 0) == 5,
        '',
        duration=9999,
    )
    n.set_controls('q back')

    return n


class StarField:
    """A field of objects that thin out over cosmological time."""

    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.objects = []
        self._populate_stelliferous()

    def _populate_stelliferous(self):
        self.objects = []
        # Galaxies: clusters of stars
        n_galaxies = random.randint(3, 7)
        for _ in range(n_galaxies):
            cx = random.randint(2, self.cols - 3)
            cy = random.randint(2, self.rows - 3)
            size = random.randint(8, 30)
            for _ in range(size):
                dx = int(random.gauss(0, 2.5))
                dy = int(random.gauss(0, 1.5))
                x = max(0, min(self.cols - 1, cx + dx))
                y = max(0, min(self.rows - 1, cy + dy))
                brightness = random.random()
                self.objects.append({
                    'x': x, 'y': y,
                    'brightness': brightness,
                    'char': random.choice(STAR_CHARS[:5]),
                    'lifespan': random.uniform(0.5, 1.0),
                })
        # Scatter stars
        for _ in range(random.randint(20, 50)):
            self.objects.append({
                'x': random.randint(0, self.cols - 1),
                'y': random.randint(0, self.rows - 1),
                'brightness': random.uniform(0.1, 0.6),
                'char': '.',
                'lifespan': random.uniform(0.3, 0.8),
            })

    def update(self, progress):
        """progress: 0.0 (start) to 1.0 (heat death). Remove objects as time advances."""
        surviving = []
        for obj in self.objects:
            if obj['lifespan'] > progress:
                # Twinkle
                if random.random() < 0.05:
                    obj['char'] = random.choice(STAR_CHARS[:max(1, int(5 * (1 - progress)))])
                surviving.append(obj)
        self.objects = surviving

        # Random nova/death flicker
        if self.objects and random.random() < 0.02:
            dying = random.choice(self.objects)
            dying['char'] = '*'
            dying['brightness'] = 1.0

    def render(self, stdscr, offset_row, offset_col, dim_factor):
        for obj in self.objects:
            ch = obj['char']
            if dim_factor < 0.3:
                ch = ' ' if random.random() > dim_factor * 3 else '.'
            elif dim_factor < 0.6:
                ch = '.' if obj['brightness'] < 0.5 else ch
            try:
                r = obj['y'] + offset_row
                c = obj['x'] + offset_col
                if dim_factor > 0.5:
                    stdscr.addstr(r, c, ch)
                else:
                    stdscr.addstr(r, c, ch, curses.A_DIM)
            except curses.error:
                pass


def run(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(100)  # slower tick for this module
    try:
        curses.start_color()
        curses.use_default_colors()
    except curses.error:
        pass

    rows, cols = stdscr.getmaxyx()
    narrator = make_heatdeath_narrator()
    field = StarField(rows - 3, cols - 2)

    # Total duration: ~300 seconds (5 min) / 100ms per tick = 3000 ticks
    total_ticks = 3000
    tick = 0
    start_time = time.monotonic()
    log_year = 0.0
    current_era = 0

    while True:
        key = stdscr.getch()
        if key == ord('q'):
            break
        elif key == curses.KEY_RESIZE:
            rows, cols = stdscr.getmaxyx()
            field = StarField(rows - 3, cols - 2)
            stdscr.clear()

        tick += 1
        progress = min(tick / total_ticks, 1.0)

        # Log-year: exponential scaling from 10^10 to 10^100
        log_year = 10 + progress * 90

        # Determine current era
        for i, (threshold, _, _) in enumerate(ERAS):
            if log_year >= threshold:
                current_era = i

        field.update(progress)

        narrator.update({
            'step': tick,
            'era': current_era,
            'progress': progress,
            'log_year': log_year,
        })

        # --- Render ---
        stdscr.erase()

        # Dim factor: 1.0 at start, approaches 0 at heat death
        dim = max(0.0, 1.0 - progress * 1.1)

        field.render(stdscr, 1, 1, dim)

        # Era title
        _, era_name, _ = ERAS[current_era]
        if era_name and dim > 0.05:
            c = max(0, (cols - len(era_name)) // 2)
            try:
                if dim > 0.5:
                    stdscr.addstr(0, c, era_name, curses.A_BOLD)
                else:
                    stdscr.addstr(0, c, era_name, curses.A_DIM)
            except curses.error:
                pass

        # Time counter
        if dim > 0.02:
            time_str = f' 10^{log_year:.0f} years'
            try:
                stdscr.addstr(rows - 2, 0, time_str[:cols - 1],
                              curses.A_DIM if dim < 0.5 else 0)
            except curses.error:
                pass

        # Narration
        narr = narrator.current_text()
        if narr and dim > 0.01:
            try:
                stdscr.addstr(rows - 1, 1, narr[:cols - 2],
                              curses.A_DIM if dim < 0.5 else 0)
            except curses.error:
                pass

        # At heat death: blank screen, blinking cursor
        if progress >= 1.0:
            stdscr.erase()
            curses.curs_set(1)
            # Just a cursor in the void. Wait for quit.
            stdscr.timeout(-1)
            while True:
                k = stdscr.getch()
                if k == ord('q'):
                    return
            break

        stdscr.refresh()
