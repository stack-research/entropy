"""Shared terminal-size guards for the curses UI."""

import curses

MIN_TERM_ROWS = 12
MIN_TERM_COLS = 50


def require_terminal_size(stdscr, min_rows=MIN_TERM_ROWS, min_cols=MIN_TERM_COLS,
                          exit_hint='q back'):
    """Return 'ok', 'wait', or 'quit' based on terminal size and user input."""
    rows, cols = stdscr.getmaxyx()
    if rows >= min_rows and cols >= min_cols:
        return 'ok'

    lines = [
        'TERMINAL TOO SMALL',
        f'Need at least {min_cols} cols x {min_rows} rows.',
        f'Current size: {cols} cols x {rows} rows.',
        '',
        'Resize the terminal to continue.',
        f'Press {exit_hint}.',
    ]

    stdscr.erase()
    start_row = max(0, (rows - len(lines)) // 2)
    for i, line in enumerate(lines):
        start_col = max(0, (cols - len(line)) // 2)
        try:
            attr = curses.A_BOLD if i == 0 else 0
            stdscr.addstr(start_row + i, start_col, line[:max(cols - start_col, 0)], attr)
        except curses.error:
            pass
    stdscr.refresh()

    key = stdscr.getch()
    if key in (ord('q'), 27):
        return 'quit'
    return 'wait'
