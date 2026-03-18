#!/usr/bin/env python3
"""ENTROPY — A Terminal Cosmology

Usage: python3 entropy.py [module]

Launches the module menu if no module is specified.
"""

import sys
import curses

MODULE_MAP = {
    'box':         'box',
    'arrow':       'arrow',
    'demon':       'demon',
    'heatdeath':   'heatdeath',
    'boltzmann':   'boltzmann',
    'selfentropy': 'selfentropy',
}


def import_module(name):
    if name == 'box':
        from modules.box import run
    elif name == 'arrow':
        from modules.arrow import run
    elif name == 'demon':
        from modules.demon import run
    elif name == 'heatdeath':
        from modules.heatdeath import run
    elif name == 'boltzmann':
        from modules.boltzmann import run
    elif name == 'selfentropy':
        from modules.selfentropy import run
    else:
        return None
    return run


def run_with_menu(stdscr):
    """Show menu, launch selected module, return to menu on quit."""
    from core.menu import run as menu_run

    while True:
        choice = menu_run(stdscr)
        if choice is None:
            break  # user quit from menu

        run_fn = import_module(choice)
        if run_fn is None:
            continue

        # Reset curses state for the module
        stdscr.clear()
        stdscr.refresh()
        run_fn(stdscr)

        # After module exits, reset curses state for menu
        stdscr.clear()
        stdscr.refresh()
        curses.curs_set(0)
        stdscr.nodelay(False)
        stdscr.timeout(-1)


def main():
    if len(sys.argv) > 1:
        module_name = sys.argv[1]
        if module_name in ('-h', '--help'):
            print(__doc__)
            sys.exit(0)
        if module_name not in MODULE_MAP:
            print(f'Unknown module: {module_name}')
            print(f'Available: {", ".join(MODULE_MAP.keys())}')
            sys.exit(1)
        run_fn = import_module(module_name)
        try:
            curses.wrapper(run_fn)
        except KeyboardInterrupt:
            pass
    else:
        try:
            curses.wrapper(run_with_menu)
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
