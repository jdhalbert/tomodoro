"""Start program by running this module or with with run()."""

import curses
import sys

from . import colors
from .tui_elements import TITLE, CommandWindow, Header, Mode, Timer, show_welcome_screen


def run(stdscr: curses.window) -> None:
    """Set up and run tomodoro.

    Args:
        stdscr (curses.window): Provided by curses.wrapper().

    """
    # curses setup
    stdscr.refresh()
    curses.curs_set(0)
    colors.init_colors()
    scn_h, scn_w = stdscr.getmaxyx()

    show_welcome_screen(message=TITLE, scn_h=scn_h, scn_w=scn_w)

    header = Header(
        [
            (TITLE, colors.DEFAULT_COLOR),
            ("s start", colors.DEFAULT_COLOR),
            ("w work", colors.WORK_COLOR),
            ("b break", colors.BREAK_COLOR),
        ],
        scn_w,
    )
    cmdwin = CommandWindow(scn_h=scn_h, scn_w=scn_w)
    timer = Timer(cmdwin=cmdwin, header=header, scn_h=scn_h, scn_w=scn_w)

    break_key = None
    while True:
        if break_key == ord("s"):
            break_key = None
        key = break_key if break_key else stdscr.getch()
        if key == ord("q"):
            sys.exit(0)
        if key == ord("s"):
            break_key = timer.start_timer_loop()
        elif key == ord("w"):
            break_key = timer.switch_mode(start=True, new_mode=Mode.WORK)
        elif key == ord("b"):
            break_key = timer.switch_mode(start=True, new_mode=Mode.BREAK)


def main() -> None:
    """Wrap run().

    Allows running as a script and installation with pipx.
    """
    curses.wrapper(run)


if __name__ == "__main__":
    main()
