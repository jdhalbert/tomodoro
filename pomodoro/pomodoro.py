import curses
from enum import Enum, auto
from time import sleep
from pomodoro import ASCII_NUM
from datetime import datetime, timedelta

HEADER_COLOR = 1
WORK_COLOR = 2
BREAK_COLOR = 3
GRAY = 244
BORDER_COLOR = 5
MODE_WORK = "work"
MODE_BREAK = "break"
DEFAULT_WORK_SECONDS = 25 * 60
DEFAULT_BREAK_SECONDS = 5 * 60

mode = MODE_WORK



def make_header(options: list[tuple[str, int]], scn_w:int, header_height:int=3, border_color:int=BORDER_COLOR) -> dict[str, curses.window]:
    """Contruct and display an app header with the provided options. Width of each box is calculated to fit on the
        screen.

    Args:
        options (list[tuple[str, int]]): Tuples of ("header option text", color_pair_identifier). The first option
            in the list should be the app title and is displayed in bold.
        scn_w (int): Screen width
        header_height (int, optional): Height of the header boxes. Defaults to 3.
        border_color (int, optional): Color pair identified for the header box borders. Defaults to BORDER_COLOR.

    Raises:
        ValueError: "Header too long for screen"

    Returns:
        dict[str, curses.window]: In format {"section text": curses.window (for that section)}
    """
    header_length = sum(len(option[0]) + 4 for option in options)
    if header_length > scn_w - 2:
        raise ValueError("Header too long for screen")
    
    cursor = int((scn_w - header_length) / 2) - 1
    sections: dict[str, curses.window] = {}
    for i, pair in enumerate(options):
        text, color_pair = pair
        section_width = len(text) + 4
        section = curses.newwin(header_height, section_width, 0, cursor)
        section.bkgd(curses.color_pair(border_color))
        section.box()
        section_format = curses.color_pair(color_pair)
        if i == 0:
            section_format = section_format | curses.A_BOLD
        section.addstr(1, 2, text, section_format)
        section.refresh()
        cursor += section_width
        sections[text] = section

    return sections


def show_welcome_screen(message:str, scn_h:int, scn_w:int, speed:float=0.25, final_sleep:float=1) -> None:
    """ Displays a blank screen and types out the given message character by character with the given time in-between.

    Args:
        message (str): App title
        scn_h (int): Screen height
        scn_w (int): Screen width
        speed (float): Seconds to sleep between printing each character to the screen
        final_sleep (float): Seconds to sleep after the entire message has been printed
    """
    curses.curs_set(1) # show a blinking cursor after the message for the cua
    welcome_screen = curses.newwin(1, len(message) + 1, int(scn_h / 2), int(scn_w / 2) - int(len(message) / 2))
    for char in message:
        welcome_screen.addch(char, curses.color_pair(HEADER_COLOR) | curses.A_BOLD)
        sleep(speed)
        welcome_screen.refresh()
    sleep(final_sleep)
    curses.curs_set(0)
    del welcome_screen


class Timer:
    seconds_left: int
    timer_windows: dict[int, curses.window]
    last_displayed_str: str

    @staticmethod
    def _pad(num:str):
        if len(num) == 1:
            return "0" + num
        return num

    @property
    def mins_str(self) -> str:
        return self._pad(str(int(self.seconds_left / 60)))
    
    @property
    def secs_str(self) -> str:
        return self._pad(str(int(self.seconds_left % 60)))
    
    @property
    def timer_str(self) -> str:
        return self.mins_str+self.secs_str
    
    def _char_pos_changed(self) -> list[int]:
        char_pos_changed = []
        current_timer_str = self.timer_str
        for i, last_char in enumerate(self.last_displayed_str):
            if current_timer_str[i] != last_char:
                char_pos_changed.append(i)
        return i

    
    def __init__(self) -> None:

            
        self.timer_windows[0].addstr(0, 0, ASCII_NUM[int(mins[0])], curses.color_pair(color))
        self.timer_windows[1].addstr(0, 0, ASCII_NUM[int(mins[1])], curses.color_pair(color))
        self.timer_windows[2].addstr(0, 0, ASCII_NUM[int(secs[0])], curses.color_pair(color))
        self.timer_windows[3].addstr(0, 0, ASCII_NUM[int(secs[1])], curses.color_pair(color))

    def set_time(self):
        #increment time
        for update_char_pos in self._char_pos_changed():
            self.timer_windows[update_char_pos].addstr(0, 0, ASCII_NUM[int(self.timer_str[update_char_pos])], curses.color_pair(color))
    
    def refresh_timer_windows(self) -> None:
        for win in self.timer_windows.values():
            win.refresh()

    

def make_timer(scn_h:int, scn_w:int) -> dict[int, curses.window]:
    """Construct a border window and windows for each timer character. The border window is not returned

    Args:
        scn_h (int): Screen height
        scn_w (int): Screen width

    Returns:
        dict[int, curses.window]: Four individual timer character windows identified by location, 0->3 left->right
    """

    # Create a window for the main content
    timer_window_height = scn_h - 6
    content_width = 11 * 4 + 2 * 3 + 1  # four characters @ 11 width/ea, three spaces between, one color
    content_height = 11
    content_y_start = int((timer_window_height - content_height) / 2) + 3 # centered under header
    content_x_start = int((scn_w - content_width) / 2)

    main_win = curses.newwin(timer_window_height, scn_w, 3, 0)
    main_win.attron(curses.color_pair(BORDER_COLOR))
    main_win.box()
    main_win.attroff(curses.color_pair(BORDER_COLOR))
    main_win.refresh()

    return {
        0: curses.newwin(10, 11, content_y_start, content_x_start),
        1: curses.newwin(10, 11, content_y_start, content_x_start + 12),
        2: curses.newwin(10, 11, content_y_start, content_x_start + 12 * 2 + 3),
        3: curses.newwin(10, 11, content_y_start, content_x_start + 12 * 3 + 3),
    }

def set_time(big_char_windows: dict[int, curses.window], seconds: int, color: int):
    mins = str(int(seconds / 60))
    secs = str(int(seconds % 60))
    if len(mins) == 1:
        mins = "0" + mins
    if len(secs) == 1:
        secs = "0" + secs


    # only update if number has changed
    big_char_windows[0].addstr(0, 0, ASCII_NUM[int(mins[0])], curses.color_pair(color))
    big_char_windows[1].addstr(0, 0, ASCII_NUM[int(mins[1])], curses.color_pair(color))
    big_char_windows[2].addstr(0, 0, ASCII_NUM[int(secs[0])], curses.color_pair(color))
    big_char_windows[3].addstr(0, 0, ASCII_NUM[int(secs[1])], curses.color_pair(color))
    for win in big_char_windows.values():
        win.refresh()


def timer_loop(
    big_char_windows: dict[int, curses.window], start_time: datetime, timer_seconds: int, input_win: curses.window
) -> int:
    end_time = start_time + timedelta(seconds=timer_seconds)
    time_left = end_time - datetime.now()
    input_win.timeout(0)
    try:
        while True:
            key = input_win.getch()
            if key == ord("s"):
                break
            time_left = end_time - datetime.now()
            set_time(big_char_windows, time_left.seconds, WORK_COLOR if mode == MODE_WORK else BREAK_COLOR)
            sleep(1)
    except KeyboardInterrupt:  # TODO don't need this if s is working to stop it
        pass
    input_win.timeout(-1)
    return time_left.seconds


def main(stdscr: curses.window):
    global mode
    seconds = DEFAULT_WORK_SECONDS

    stdscr.refresh()

    # Hide the cursor
    curses.curs_set(0)

    # Define color pairs
    curses.init_pair(HEADER_COLOR, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(BREAK_COLOR, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(WORK_COLOR, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(BORDER_COLOR, GRAY, curses.COLOR_BLACK)

    # Get screen dimensions
    scn_h, scn_w = stdscr.getmaxyx()

    # show_welcome_screen(height, width)

    header = make_header(
        [
            ("pomodoro.", HEADER_COLOR),
            ("s start/stop", HEADER_COLOR),
            ("w work", WORK_COLOR),
            ("b break", BREAK_COLOR),
        ],
        scn_w,
    )
    big_char_windows = make_timer(scn_h, scn_w)
    set_time(big_char_windows, DEFAULT_WORK_SECONDS, WORK_COLOR)

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
        elif key == ord("s"):
            seconds = timer_loop(big_char_windows, datetime.now(), seconds, input_win)
            if seconds == 0:
                seconds = DEFAULT_WORK_SECONDS if mode == MODE_WORK else DEFAULT_BREAK_SECONDS
        elif key == ord("w"):
            mode = MODE_WORK
            input_win.clear()
            input_str = f"Work minutes [{int(DEFAULT_WORK_SECONDS/60)}]: ? "
            input_win.addstr(1, 2, input_str)
            input_win.box()  # fix this TODO
            input_win.refresh()
            curses.curs_set(1)
            curses.echo()
            try:
                seconds = int(input_win.getstr(1, 2 + len(input_str), 2).decode(encoding="utf-8")) * 60
            except Exception:
                seconds = DEFAULT_WORK_SECONDS
            curses.curs_set(0)
            curses.noecho()
            input_win.clear()
            input_win.box()
            input_win.addstr(1, 2, "Enter command (q to quit) ")
            input_win.refresh()
            set_time(big_char_windows, seconds, WORK_COLOR)
        elif key == ord("c"):  # continue to other mode
            pass  # switch mode, proceed as if that button was pressed
        elif key == ord("b"):
            mode = MODE_BREAK
            input_win.clear()
            input_str = "Break minutes [{int(DEFAULT_WORK_SECONDS/60)}]: ? "
            input_win.addstr(1, 2, input_str)
            input_win.box()  # fix this TODO
            input_win.refresh()
            curses.curs_set(1)
            curses.echo()
            try:
                seconds = int(input_win.getstr(1, 2 + len(input_str), 2).decode(encoding="utf-8")) * 60
            except Exception:
                seconds = DEFAULT_BREAK_SECONDS
            curses.curs_set(0)
            curses.noecho()
            input_win.clear()
            input_win.box()
            input_win.addstr(1, 2, "Enter command (q to quit) ")
            input_win.refresh()
            set_time(big_char_windows, seconds, BREAK_COLOR)

        elif key == ord("h"):
            header = make_header(scn_h, scn_w)

class Mode(Enum):
    BREAK = auto()
    WORK = auto()


class ClockNumberWindow:


class Input:
    pass

class ClockWin:

    


    mode: Mode

    def __init__(self) -> None:
        self.mode = Mode.WORK

    def set_clock(self):



if __name__ == "__main__":
    curses.wrapper(main)
