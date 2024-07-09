import curses
from time import sleep
from pomodoro import ASCII_NUM
from datetime import datetime, timedelta

HEADER_COLOR = 1
PRODUCT_COLOR = 2
GRAY = 244
BORDER_COLOR = 3


def make_header(title: str, options: list[str], scn_w) -> dict[str, curses.window]:
    # Create a window for the header
    # Get screen dimensions

    options.insert(0, title)
    header_height = 3
    header_length = sum(len(option) + 4 for option in options)
    cursor = int((scn_w - header_length) / 2) - 1

    if header_length > scn_w - 2:
        raise ValueError("Header too long")

    sections: dict[str, curses.window] = {}
    for i, option in enumerate(options):
        section_contents = option
        section_width = len(section_contents) + 4
        section = curses.newwin(header_height, section_width, 0, cursor)
        section.bkgd(curses.color_pair(BORDER_COLOR))
        section.box()
        section_format = curses.color_pair(HEADER_COLOR)
        if i == 0:
            section_format = section_format | curses.A_BOLD
        section.addstr(1, 2, section_contents, section_format)
        section.refresh()
        cursor += section_width
        sections[section_contents] = section

    return sections


def show_welcome_screen(scn_h, scn_w) -> None:
    curses.curs_set(1)
    message = "pomodoro."
    welcome_screen = curses.newwin(1, len(message) + 1, int(scn_h / 2), int(scn_w / 2) - int(len(message) / 2))
    for char in message:
        welcome_screen.addch(char, curses.color_pair(HEADER_COLOR) | curses.A_BOLD)
        sleep(0.25)
        welcome_screen.refresh()
    sleep(1)
    curses.curs_set(0)
    del welcome_screen


def make_timer_window(scn_h, scn_w) -> dict[int, curses.window]:
    # Create a window for the main content
    timer_window_height = scn_h - 6
    content_width = 11 * 4 + 2 * 3 + 1  # four characters, three spaces, one color
    content_height = 11
    content_y_start = int((timer_window_height - content_height) / 2) + 3
    content_x_start = int((scn_w - content_width) / 2)
    main_win = curses.newwin(timer_window_height, scn_w, 3, 0)
    main_win.attron(curses.color_pair(BORDER_COLOR))
    main_win.box()
    main_win.attroff(curses.color_pair(BORDER_COLOR))
    big_char_positions = {0: ASCII_NUM[2], 1: ASCII_NUM[5], 2: ASCII_NUM[0], 3: ASCII_NUM[0]}
    big_char_windows = {
        0: curses.newwin(10, 11, content_y_start, content_x_start),
        1: curses.newwin(10, 11, content_y_start, content_x_start + 12),
        2: curses.newwin(10, 11, content_y_start, content_x_start + 12 * 2 + 3),
        3: curses.newwin(10, 11, content_y_start, content_x_start + 12 * 3 + 3),
    }
    main_win.refresh()
    for pos, win in big_char_windows.items():
        win.addstr(big_char_positions[pos])
        win.refresh()
    return big_char_windows


def timer_loop(big_char_windows: dict[int, curses.window], start_time: datetime, timer_minutes: int):
    end_time = start_time + timedelta(minutes=timer_minutes)
    try:
        while True:
            time_left = end_time - datetime.now()
            mins = str(int(time_left.seconds / 60))
            secs = str(int(time_left.seconds % 60))
            if len(mins) == 1:
                mins = "0" + mins
            if len(secs) == 1:
                secs = "0" + secs
            big_char_windows[0].addstr(0, 0, ASCII_NUM[int(mins[0])])
            big_char_windows[1].addstr(0, 0, ASCII_NUM[int(mins[1])])
            big_char_windows[2].addstr(0, 0, ASCII_NUM[int(secs[0])])
            big_char_windows[3].addstr(0, 0, ASCII_NUM[int(secs[1])])
            for win in big_char_windows.values():
                win.refresh()
            sleep(1)  # fix this and go off time since start
    except KeyboardInterrupt:
        pass


def main(stdscr: curses.window):
    work_minutes = 25

    stdscr.refresh()

    # Hide the cursor
    curses.curs_set(0)

    # Define color pairs
    curses.init_pair(HEADER_COLOR, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(PRODUCT_COLOR, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(BORDER_COLOR, GRAY, curses.COLOR_BLACK)

    # Get screen dimensions
    scn_h, scn_w = stdscr.getmaxyx()

    # show_welcome_screen(height, width)

    header = make_header("pomodoro.", ["s start/stop", "w work minutes", "b break minutes"], scn_w)
    big_char_windows = make_timer_window(scn_h, scn_w)

    # Create a window for user input
    input_win = curses.newwin(3, scn_w, scn_h - 3, 0)
    input_win.box()
    input_win.addstr(1, 2, "Selection option (q to quit): ")
    input_win.refresh()

    stdscr.refresh()

    while True:
        key = stdscr.getch()
        if key == ord("q"):
            break
        elif key == [ord("s")]:
            timer_loop(big_char_windows, datetime.now(), work_minutes)
        elif key == ord("w"):
            input_win.clear()
            input_win.addstr(1, 2, "How many minutes? ")
            input_win.refresh()
            curses.curs_set(1)
            work_minutes = stdscr.getstr()
            curses.curs_set(0)
        elif key in [ord("1"), ord("2"), ord("3")]:
            product_index = int(chr(key)) - 1
            timer_win.addstr(scn_h - 7, 2, f"You selected: {products[product_index]['name']}")
            timer_win.refresh()
        elif key == ord("d"):
            del header
            timer_win.touchwin()
            timer_win.refresh()
        elif key == ord("h"):
            header = make_header(scn_h, scn_w)


if __name__ == "__main__":
    curses.wrapper(main)
