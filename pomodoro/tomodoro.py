from __future__ import annotations
import curses
from enum import Enum, auto
from time import sleep
from pomodoro import ASCII_NUM
from datetime import datetime, timedelta

HEADER_COLOR = 1

GRAY = 244
BORDER_COLOR = 5
BREAK_COLOR = 3
WORK_COLOR = 2

DEFAULT_WORK_MINUTES = 25
DEFAULT_BREAK_MINUTES = 5


def make_header(
    options: list[tuple[str, int]], scn_w: int, header_height: int = 3, border_color: int = BORDER_COLOR
) -> dict[int, curses.window]:
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
        dict[int, curses.window]: In format {position: curses.window (for that section)}
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
        sections[i] = section

    return sections


def show_welcome_screen(message: str, scn_h: int, scn_w: int, speed: float = 0.25, final_sleep: float = 1) -> None:
    """Displays a blank screen and types out the given message character by character with the given time in-between.

    Args:
        message (str): App title
        scn_h (int): Screen height
        scn_w (int): Screen width
        speed (float): Seconds to sleep between printing each character to the screen
        final_sleep (float): Seconds to sleep after the entire message has been printed
    """
    curses.curs_set(1)  # show a blinking cursor after the message for the cua
    welcome_screen = curses.newwin(1, len(message) + 1, int(scn_h / 2), int(scn_w / 2) - int(len(message) / 2))
    for char in message:
        welcome_screen.addch(char, curses.color_pair(HEADER_COLOR) | curses.A_BOLD)
        sleep(speed)
        welcome_screen.refresh()
    sleep(final_sleep)
    curses.curs_set(0)
    del welcome_screen


class Timer:

    mode: Mode
    # start_time: datetime
    end_time: datetime
    set_seconds: int
    timer_windows: dict[int, curses.window]
    last_displayed_str: str
    cmdwin: CommandWindow

    @staticmethod
    def _pad(num: str):
        if len(num) == 1:
            return "0" + num
        return num

    @property
    def color_pair(self) -> int:
        color = BREAK_COLOR if self.mode == Mode.BREAK else WORK_COLOR
        return curses.color_pair(color)

    @property
    def seconds_left(self) -> int:
        return (self.end_time - datetime.now()).seconds

    @property
    def mins_str(self) -> str:
        return self._pad(str(int(self.seconds_left / 60)))

    @property
    def secs_str(self) -> str:
        return self._pad(str(int(self.seconds_left % 60)))

    @property
    def timer_str(self) -> str:
        return self.mins_str + self.secs_str

    def _char_pos_changed(self) -> list[int]:
        char_pos_changed = []
        current_timer_str = self.timer_str
        for i, last_char in enumerate(self.last_displayed_str):
            if current_timer_str[i] != last_char:
                char_pos_changed.append(i)
        return char_pos_changed

    def __init__(self, cmdwin: CommandWindow, scn_h: int, scn_w: int, minutes: int = 25) -> None:
        self.mode = Mode.WORK
        self.cmdwin = cmdwin
        self._make_timer_windows(scn_h=scn_h, scn_w=scn_w, minutes=minutes)
        self.set_timer(minutes=minutes)
        self._refresh_timer_windows(initial=True)

    def set_timer(self, minutes: int):
        # self.set_seconds = minutes * 60
        self.set_seconds = minutes * 60 + 1  # round up
        self.end_time = datetime.now() + timedelta(seconds=self.set_seconds)
        self._refresh_timer_windows(initial=True)

    def _refresh_timer_windows(self, initial: bool = False) -> None:
        pos_changed = [0, 1, 2, 3] if initial else self._char_pos_changed()
        for update_char_pos in pos_changed:
            win = self.timer_windows[update_char_pos]
            win.addstr(0, 0, ASCII_NUM[int(self.timer_str[update_char_pos])], self.color_pair)
            win.refresh()
        self.last_displayed_str = self.timer_str

    def start_timer_loop(self) -> int:
        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(seconds=self.set_seconds)
        self.cmdwin.win.timeout(0)  # make control input non-blocking
        try:
            while True:
                key = self.cmdwin.win.getch()
                if key == ord("s"):
                    break
                self._refresh_timer_windows()
                self.set_seconds = self.seconds_left
                sleep(0.5)
        except KeyboardInterrupt:  # TODO don't need this if s is working to stop it
            pass
        self.cmdwin.win.timeout(-1)  # make control input blocking again

    def _make_timer_windows(self, scn_h: int, scn_w: int, minutes: int) -> dict[int, curses.window]:
        """Construct a border window and windows for each timer character. The border window is not returned

        Args:
            scn_h (int): Screen height
            scn_w (int): Screen width
            minutes (int): Initial timer setting

        Returns:
            dict[int, curses.window]: Four individual timer character windows identified by location, 0->3 left->right
        """

        # Create a window for the main content
        timer_window_height = scn_h - 6
        content_width = 11 * 4 + 2 * 3 + 1  # four characters @ 11 width/ea, three spaces between, one color
        content_height = 11
        content_y_start = int((timer_window_height - content_height) / 2) + 3  # centered under header
        content_x_start = int((scn_w - content_width) / 2)

        main_win = curses.newwin(timer_window_height, scn_w, 3, 0)
        main_win.attron(curses.color_pair(BORDER_COLOR))
        main_win.box()
        main_win.attroff(curses.color_pair(BORDER_COLOR))
        main_win.refresh()

        self.timer_windows = {
            0: curses.newwin(10, 11, content_y_start, content_x_start),
            1: curses.newwin(10, 11, content_y_start, content_x_start + 12),
            2: curses.newwin(10, 11, content_y_start, content_x_start + 12 * 2 + 3),
            3: curses.newwin(10, 11, content_y_start, content_x_start + 12 * 3 + 3),
        }


class CommandWindow:

    win: curses.window
    prompt: str

    def __init__(self, scn_h: int, scn_w: int) -> None:
        self.win = curses.newwin(3, scn_w, scn_h - 3, 0)
        self.change_prompt()

    def change_prompt(self, prompt: str = "Select option (q to quit)") -> None:
        self.prompt = prompt
        self.win.clear()
        self.win.box()
        self.win.addstr(1, 2, prompt)
        self.win.refresh()

    def getmins(self) -> int:
        return int(self.win.getstr(1, 2 + len(self.prompt), 2).decode(encoding="utf-8"))


def main(stdscr: curses.window):

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
            ("tomodoro.", HEADER_COLOR),
            ("s start", HEADER_COLOR),
            ("w work", WORK_COLOR),
            ("b break", BREAK_COLOR),
        ],
        scn_w,
    )

    stdscr.refresh()

    # Create a window for user input
    cmdwin = CommandWindow(scn_h=scn_h, scn_w=scn_w)
    timer = Timer(cmdwin=cmdwin, scn_h=scn_h, scn_w=scn_w, minutes=25)

    while True:
        key = stdscr.getch()
        if key == ord("q"):
            break
        elif key == ord("s"):
            # header[1].clear()
            header[1].addstr(1, 2, "s stop ", curses.color_pair(HEADER_COLOR))
            header[1].refresh()
            timer.start_timer_loop()
            header[1].addstr(1, 2, "s start", curses.color_pair(HEADER_COLOR))
            header[1].refresh()  # TODO functionize
        elif key == ord("w"):
            timer.mode = Mode.WORK  # TODO fix
            cmdwin.change_prompt(f"Work minutes [{int(DEFAULT_WORK_MINUTES)}]: ? ")
            curses.curs_set(1)
            curses.echo()
            try:
                minutes = cmdwin.getmins()
            except Exception:
                minutes = DEFAULT_WORK_MINUTES
            curses.curs_set(0)
            curses.noecho()
            cmdwin.change_prompt()
            timer.set_timer(minutes=minutes)
        elif key == ord("c"):  # continue to other mode
            pass  # switch mode, proceed as if that button was pressed
        elif key == ord("b"):
            timer.mode = Mode.BREAK
            cmdwin.change_prompt(f"Break minutes [{int(DEFAULT_BREAK_MINUTES)}]: ? ")
            curses.curs_set(1)
            curses.echo()
            try:
                minutes = cmdwin.getmins()
            except Exception:
                minutes = DEFAULT_BREAK_MINUTES
            curses.curs_set(0)
            curses.noecho()
            cmdwin.change_prompt()
            timer.set_timer(minutes=minutes)


class Mode(Enum):
    BREAK = auto()
    WORK = auto()


if __name__ == "__main__":
    curses.wrapper(main)
