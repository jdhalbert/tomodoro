"""Curses colors definitions and setup."""

import curses

# Custom color codes (see https://www.ditig.com/publications/256-colors-cheat-sheet_)
GRAY50 = 244

# Curses color pair numbers
DEFAULT_COLOR = 1
WORK_COLOR = 2
BREAK_COLOR = 3
GRAY_COLOR = 4
WHITE_COLOR = 5


def init_colors() -> None:
    """Set up curses color pairs."""
    curses.init_pair(DEFAULT_COLOR, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(WORK_COLOR, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(BREAK_COLOR, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(GRAY_COLOR, GRAY50, curses.COLOR_BLACK)
    curses.init_pair(WHITE_COLOR, curses.COLOR_WHITE, curses.COLOR_WHITE)
