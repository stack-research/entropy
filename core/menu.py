"""Main menu with ASCII art title and module selection."""

import curses
import random

TITLE = [
    r"  _____ _   _ _____ ____   ___  ______   __",
    r" | ____| \ | |_   _|  _ \ / _ \|  _ \ \ / /",
    r" |  _| |  \| | | | | |_) | | | | |_) \ V / ",
    r" | |___| |\  | | | |  _ <| |_| |  __/ | |  ",
    r" |_____|_| \_| |_| |_| \_\\___/|_|    |_|  ",
]

SUBTITLE = "A Terminal Cosmology"

MODULES = [
    ('box',        'The Box',           'Watch order dissolve into equilibrium'),
    ('arrow',      'Arrow of Time',     'Which direction is real?'),
    ('demon',      'Maxwell\'s Demon',  'Become the demon. Sort the particles. Lose.'),
    ('heatdeath',  'Heat Death',        'Watch the universe end'),
    ('boltzmann',  'Boltzmann Brain',   'Wait for a fluctuation in the void'),
    ('selfentropy','Self-Entropy',      'The simulation measures its own cost'),
]

FOOTER_HINTS = [
    "S = k_B ln \u03a9",
    "The second law is statistical, not dynamical.",
    "The only law of physics that knows about time.",
    "Boltzmann: \"I am conscious of being only an individual struggling weakly against the stream of time.\"",
    "The universe is a cooling ember.",
    "You are a low-entropy fluctuation.",
    "Your brain generates more entropy reading this than the information contains.",
]


def run(stdscr):
    """Display menu and return the selected module name."""
    curses.curs_set(0)
    stdscr.timeout(-1)  # blocking input
    try:
        curses.start_color()
        curses.use_default_colors()
    except curses.error:
        pass

    selected = 0
    hint = random.choice(FOOTER_HINTS)

    while True:
        stdscr.erase()
        rows, cols = stdscr.getmaxyx()

        # --- Title ---
        title_start_row = max(1, (rows - len(TITLE) - len(MODULES) - 10) // 2)
        for i, line in enumerate(TITLE):
            c = max(0, (cols - len(line)) // 2)
            try:
                stdscr.addstr(title_start_row + i, c, line)
            except curses.error:
                pass

        # --- Subtitle ---
        sub_row = title_start_row + len(TITLE) + 1
        c = max(0, (cols - len(SUBTITLE)) // 2)
        try:
            stdscr.addstr(sub_row, c, SUBTITLE)
        except curses.error:
            pass

        # --- Divider ---
        div_row = sub_row + 2
        div = "\u2500" * min(44, cols - 4)
        c = max(0, (cols - len(div)) // 2)
        try:
            stdscr.addstr(div_row, c, div)
        except curses.error:
            pass

        # --- Module list ---
        list_start = div_row + 2
        for i, (key, name, desc) in enumerate(MODULES):
            row = list_start + i * 2
            if row >= rows - 3:
                break

            num = f"  [{i + 1}]  "
            label = f"{name:<20s}{desc}"
            if i == selected:
                prefix = " \u25b6 "
                line = f"{prefix}{num}{label}"
            else:
                prefix = "   "
                line = f"{prefix}{num}{label}"

            line = line[:cols - 1]
            c = max(0, (cols - 60) // 2)
            try:
                if i == selected:
                    stdscr.addstr(row, c, line, curses.A_BOLD)
                else:
                    stdscr.addstr(row, c, line)
            except curses.error:
                pass

        # --- Footer hint ---
        hint_row = rows - 2
        hint_text = hint[:cols - 4]
        c = max(0, (cols - len(hint_text)) // 2)
        try:
            stdscr.addstr(hint_row, c, hint_text)
        except curses.error:
            pass

        # --- Navigation help ---
        nav = "\u2191/\u2193 select   ENTER launch   q quit"
        c = max(0, (cols - len(nav)) // 2)
        try:
            stdscr.addstr(rows - 1, c, nav)
        except curses.error:
            pass

        stdscr.refresh()

        # --- Input ---
        key = stdscr.getch()

        if key in (ord('q'), 27):  # q or ESC
            return None
        elif key == curses.KEY_UP or key == ord('k'):
            selected = (selected - 1) % len(MODULES)
        elif key == curses.KEY_DOWN or key == ord('j'):
            selected = (selected + 1) % len(MODULES)
        elif key in (curses.KEY_ENTER, 10, 13):
            return MODULES[selected][0]
        elif ord('1') <= key <= ord('6'):
            idx = key - ord('1')
            if idx < len(MODULES):
                return MODULES[idx][0]
