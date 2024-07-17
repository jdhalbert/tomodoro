"""Start program by running this module or with with run()."""

import curses

from tomodoro import colors
from tomodoro.tui_elements import (
    TITLE,
    CommandWindow,
    Header,
    Mode,
    Timer,
    show_welcome_screen,
)


def main(stdscr: curses.window):

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

    while True:
        key = stdscr.getch()
        if key == ord("q"):
            break
        elif key == ord("s"):
            timer.start_timer_loop()
        elif key == ord("w"):
            timer.switch_mode(new_mode=Mode.WORK)
        elif key == ord("b"):
            timer.switch_mode(new_mode=Mode.BREAK)


def run():
    """Wrapper allows running as a script and installation with pipx."""
    curses.wrapper(main)


if __name__ == "__main__":
    run()
