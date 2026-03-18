"""Module 4: Heat Death Terminal.

Cosmological timescales compressed into ~5 minutes. Stars form, burn, die.
Black holes evaporate. The last photons red-shift into nothing.
The terminal slowly dims. Text gets sparser. Eventually — nothing.
Just a cursor blinking in void.

A hidden ParticleSystem tracks real thermodynamics underneath.
The star field is the poetry. The engine is the physics."""

import curses
import random
import numpy as np
from core.engine import ParticleSystem, K_B
from core.narrator import Narrator

# Cosmological eras: (log-year threshold, name, particle fraction)
ERAS = [
    (0,   'STELLIFEROUS ERA',   1.00),
    (14,  'DEGENERATE ERA',     0.50),
    (25,  'BLACK HOLE ERA',     0.15),
    (40,  'DARK ERA',           0.03),
    (60,  'ASYMPTOTIC SILENCE', 0.005),
    (100, 'HEAT DEATH',         0.00),
]

STAR_CHARS = ['*', '+', '.', '\u00b7', '\u2219', '\u2022', '\u25e6']


def make_heatdeath_narrator():
    n = Narrator()
    n.add_rule(
        lambda s: s.get('era', 0) == 0 and s.get('step', 0) > 10,
        'Ten billion years per second. The sun is already gone.',
        duration=150,
    )
    n.add_rule(
        lambda s: s.get('era', 0) >= 1 and s.get('prev_era', 0) == 0,
        'Stellar nucleosynthesis ends. No new atoms will be forged.',
        duration=180,
    )
    n.add_rule(
        lambda s: s.get('era', 0) >= 2 and s.get('prev_era', 0) <= 1,
        'Black holes: the last engines of entropy. They, too, are temporary.',
        duration=180,
    )
    n.add_rule(
        lambda s: s.get('era', 0) >= 3 and s.get('prev_era', 0) <= 2,
        'The photon wavelength exceeds the observable universe. Light forgets itself.',
        duration=200,
    )
    n.add_rule(
        lambda s: s.get('era', 0) >= 4 and s.get('prev_era', 0) <= 3,
        'Maximum entropy. Thermal equilibrium. The arrow of time dissolves.',
        duration=250,
    )
    n.set_controls('q back')
    return n


class StarField:
    """Visual layer: a field of stars that thin out over cosmological time."""

    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.objects = []
        self._populate()

    def _populate(self):
        self.objects = []
        if self.rows <= 0 or self.cols <= 0:
            return

        if self.rows < 5 or self.cols < 8:
            n_stars = random.randint(1, max(1, min(self.rows * self.cols, 8)))
            for _ in range(n_stars):
                self.objects.append({
                    'x': random.randint(0, self.cols - 1),
                    'y': random.randint(0, self.rows - 1),
                    'brightness': random.uniform(0.1, 0.7),
                    'char': random.choice(STAR_CHARS[:3]),
                    'lifespan': random.uniform(0.2, 0.8),
                })
            return

        # Galaxy clusters
        n_galaxies = random.randint(4, 8)
        for _ in range(n_galaxies):
            cx = random.randint(3, self.cols - 4)
            cy = random.randint(2, self.rows - 3)
            size = random.randint(8, 30)
            for _ in range(size):
                dx = int(random.gauss(0, 2.5))
                dy = int(random.gauss(0, 1.5))
                x = max(0, min(self.cols - 1, cx + dx))
                y = max(0, min(self.rows - 1, cy + dy))
                self.objects.append({
                    'x': x, 'y': y,
                    'brightness': random.random(),
                    'char': random.choice(STAR_CHARS[:5]),
                    'lifespan': random.uniform(0.4, 1.0),
                })
        # Scattered field stars
        for _ in range(random.randint(20, 50)):
            self.objects.append({
                'x': random.randint(0, self.cols - 1),
                'y': random.randint(0, self.rows - 1),
                'brightness': random.uniform(0.1, 0.5),
                'char': '.',
                'lifespan': random.uniform(0.2, 0.7),
            })

    def update(self, progress):
        """Remove stars whose lifespan has passed. Occasional nova flicker."""
        surviving = []
        for obj in self.objects:
            if obj['lifespan'] > progress:
                # Twinkle
                if random.random() < 0.04:
                    depth = max(1, int(5 * (1 - progress)))
                    obj['char'] = random.choice(STAR_CHARS[:depth])
                surviving.append(obj)
        self.objects = surviving

        # Nova: a dying star flares briefly
        if self.objects and random.random() < 0.02:
            dying = random.choice(self.objects)
            dying['char'] = '*'
            dying['brightness'] = 1.0

    def render(self, stdscr, offset_row, offset_col, dim):
        for obj in self.objects:
            ch = obj['char']
            if dim < 0.3:
                if random.random() > dim * 3:
                    continue
                ch = '.'
            elif dim < 0.6:
                ch = '.' if obj['brightness'] < 0.5 else ch
            try:
                r = obj['y'] + offset_row
                c = obj['x'] + offset_col
                attr = 0 if dim > 0.5 else curses.A_DIM
                stdscr.addstr(r, c, ch, attr)
            except curses.error:
                pass


def run(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(100)
    try:
        curses.start_color()
        curses.use_default_colors()
    except curses.error:
        pass

    rows, cols = stdscr.getmaxyx()
    canvas_rows = max(rows - 4, 1)
    canvas_cols = max(cols - 2, 1)

    narrator = make_heatdeath_narrator()
    field = StarField(canvas_rows, canvas_cols)

    # Hidden physics engine tracking real thermodynamics
    initial_n = 300
    engine = ParticleSystem(
        initial_n, (canvas_cols * 2, canvas_rows * 4),
        initial_config='uniform',
        temperature=2.0,
        collisions=True,
        collision_radius=3.0,
    )

    total_ticks = 3000
    tick = 0
    current_era = 0
    prev_era = 0
    last_cull_tick = 0

    while True:
        key = stdscr.getch()
        if key == ord('q'):
            break
        elif key == curses.KEY_RESIZE:
            rows, cols = stdscr.getmaxyx()
            canvas_rows = max(rows - 4, 1)
            canvas_cols = max(cols - 2, 1)
            field = StarField(canvas_rows, canvas_cols)
            engine = ParticleSystem(
                initial_n, (canvas_cols * 2, canvas_rows * 4),
                initial_config='uniform', temperature=2.0,
                collisions=True, collision_radius=3.0,
            )
            tick = 0
            narrator = make_heatdeath_narrator()
            stdscr.clear()

        tick += 1
        progress = min(tick / total_ticks, 1.0)
        log_year = 10 + progress * 90

        # Determine era
        prev_era = current_era
        for i, (threshold, _, _) in enumerate(ERAS):
            if log_year >= threshold:
                current_era = i

        # --- Evolve the hidden engine ---
        if engine.n > 0:
            engine.step()

        # Cool the universe
        if tick % 10 == 0 and progress > 0.05:
            engine.vel *= 0.995

        # Cull engine particles to match era
        if tick % 30 == 0 and tick != last_cull_tick:
            last_cull_tick = tick
            _, _, target_frac = ERAS[current_era]
            target_n = max(0, int(initial_n * target_frac))
            if engine.n > target_n and engine.n > 1:
                to_remove = min(max(1, (engine.n - target_n) // 10), engine.n - 1)
                keep = np.random.choice(engine.n, engine.n - to_remove, replace=False)
                keep.sort()
                engine.pos = engine.pos[keep]
                engine.vel = engine.vel[keep]
                engine.n = len(keep)

        # --- Evolve the visual star field ---
        field.update(progress)

        # Engine stats
        temp = engine.measured_temperature() if engine.n > 0 else 0.0
        entropy_norm = engine.entropy_normalized() if engine.n > 1 else 1.0

        narrator.update({
            'step': tick,
            'era': current_era,
            'prev_era': prev_era,
            'progress': progress,
            'log_year': log_year,
        })

        # --- Render ---
        stdscr.erase()
        dim = max(0.0, 1.0 - progress * 1.1)

        # Star field (the poetry)
        field.render(stdscr, 1, 1, dim)

        # Era title
        _, era_name, _ = ERAS[current_era]
        if era_name and dim > 0.05:
            c = max(0, (cols - len(era_name)) // 2)
            try:
                attr = curses.A_BOLD if dim > 0.5 else curses.A_DIM
                stdscr.addstr(0, c, era_name, attr)
            except curses.error:
                pass

        # Status: real physics from the hidden engine
        status_row = min(canvas_rows + 1, rows - 3)
        if dim > 0.02:
            time_str = f' 10^{log_year:.0f} years'
            stats = f'  T={temp:.4f}  S/Smax={entropy_norm:.3f}'
            line = time_str + stats
            try:
                attr = curses.A_DIM if dim < 0.5 else 0
                stdscr.addstr(status_row, 0, line[:cols - 1], attr)
            except curses.error:
                pass

        # Narration
        narr = narrator.current_text()
        if narr and dim > 0.01:
            narr_row = min(status_row + 1, rows - 1)
            try:
                attr = curses.A_DIM if dim < 0.5 else 0
                stdscr.addstr(narr_row, 1, narr[:cols - 2], attr)
            except curses.error:
                pass

        # Heat death: void
        if progress >= 1.0:
            stdscr.erase()
            curses.curs_set(1)
            stdscr.timeout(-1)
            while True:
                k = stdscr.getch()
                if k == ord('q'):
                    return
            break

        stdscr.refresh()
