from __future__ import annotations
import curses
from enum import Enum
from time import sleep
from tomodoro import ASCII_NUM
from datetime import datetime, timedelta
from contextlib import contextmanager

TITLE = "tomodoro."

GRAY = 244

DEFAULT_COLOR = 1
WORK_COLOR = 2
BREAK_COLOR = 3
GRAY_COLOR = 4
WHITE_COLOR = 5


class Mode(Enum):
    """Timer modes"""

    BREAK = "Break"
    WORK = "Work"


def show_welcome_screen(message: str, scn_h: int, scn_w: int, speed: float = 0.15, final_sleep: float = 1) -> None:
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
        welcome_screen.addch(char, curses.color_pair(DEFAULT_COLOR) | curses.A_BOLD)
        sleep(speed)
        welcome_screen.refresh()
    sleep(final_sleep)
    curses.curs_set(0)
    del welcome_screen


@contextmanager
def echo_and_cursor_on():
    """Within the context manager, turn on echoing of input to the screen and a blinking cursor."""
    try:
        curses.echo()
        curses.curs_set(1)
        yield
    finally:
        curses.noecho()
        curses.curs_set(0)


class Timer:
    """Main timer window including character windows"""

    scn_h: int
    scn_w: int
    mode: Mode
    mode_properties: dict[Mode, dict[str, int]]
    end_time: datetime
    set_seconds: int
    last_displayed_time_str: str
    cmdwin: CommandWindow
    header: Header
    timer_border_window: curses.window
    timer_windows: dict[int, curses.window]

    @staticmethod
    def _pad(num: str) -> str:
        """Pad a single digit string with a leading zero.

        Args:
            num (str): To pad

        Returns:
            str: Padded string
        """
        if len(num) == 1:
            return "0" + num
        return num

    @property
    def _mode_color_pair(self) -> int:
        """curses.color_pair() configured for the current mode.

        Returns:
            int: curses color_pair
        """
        return curses.color_pair(self.mode_properties[self.mode]["color"])

    @property
    def _seconds_left(self) -> int:
        """Seconds between now and the timer's end time.

        Returns:
            int: Seconds
        """
        return (self.end_time - datetime.now()).seconds

    @property
    def _mins_str(self) -> str:
        """Two-digit timer display minutes.

        Returns:
            str: Minutes (MM)
        """
        return self._pad(str(int(self._seconds_left / 60)))

    @property
    def _secs_str(self) -> str:
        """Two-digit timer display seconds.

        Returns:
            str: Seconds (SS)
        """
        return self._pad(str(int(self._seconds_left % 60)))

    @property
    def _timer_str(self) -> str:
        """Full four-digit timer display.

        Returns:
            str: (MMSS)
        """
        return self._mins_str + self._secs_str

    def _char_pos_changed(self) -> list[int]:
        """Get the position numbers of the displayed timer windows that need to be updated to show the new current
            time. Used to prevent all four timer number positions from being updated every second.

        Returns:
            list[int]: Timer window position numbers needing refresh
        """
        char_pos_changed = []
        current_timer_str = self._timer_str
        for i, last_char in enumerate(self.last_displayed_time_str):
            if current_timer_str[i] != last_char:
                char_pos_changed.append(i)
        return char_pos_changed

    def __init__(
        self,
        cmdwin: CommandWindow,
        header: Header,
        scn_h: int,
        scn_w: int,
        work_minutes: int = 25,
        break_minutes: int = 5,
        break_color: int = BREAK_COLOR,
        work_color: int = WORK_COLOR,
    ) -> None:
        self.scn_h = scn_h
        self.scn_w = scn_w
        self.cmdwin = cmdwin
        self.header = header
        self.mode = Mode.WORK
        self.mode_properties = {
            Mode.BREAK: {"minutes": break_minutes, "color": break_color, "cmdwin_prompt": "On break..."},
            Mode.WORK: {"minutes": work_minutes, "color": work_color, "cmdwin_prompt": "Working..."},
        }

        self._make_timer_windows(scn_h=scn_h, scn_w=scn_w)
        self.set_timer(minutes=work_minutes)
        self._refresh_timer_windows(initial=True)

    def _refresh_timer_windows(self, initial: bool = False) -> None:
        """Update timer character windows to reflect the current time left. Updates only windows where the
            character needs to change.

        Args:
            initial (bool, optional): Set True if setting all four characters for the first time. Defaults to False.
        """
        pos_changed = [0, 1, 2, 3] if initial else self._char_pos_changed()
        for update_char_pos in pos_changed:
            win = self.timer_windows[update_char_pos]
            win.addstr(0, 0, ASCII_NUM[int(self._timer_str[update_char_pos])], self._mode_color_pair)
            win.refresh()
        self.last_displayed_time_str = self._timer_str

    def set_timer(self, minutes: int):
        """Set the timer to given number of minutes and refresh the timer display.

        Args:
            minutes (int)
        """
        self.set_seconds = minutes * 60 + 1  # prevent rounding down displayed value due to integer math
        self.end_time = datetime.now() + timedelta(seconds=self.set_seconds)
        self._refresh_timer_windows(initial=True)

    def _alarm(self) -> None:
        """Alert used to indicate timer has reached zero."""
        print("\a")  # beep
        # TODO - implement flashing screen

    def start_timer_loop(self) -> None:
        """Start the timer countdown loop. Temporary changes made to visual display while loop runs."""

        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(seconds=self.set_seconds)

        with self.cmdwin._temp_change():
            with self.header._temp_change():
                self.cmdwin.win.timeout(0)  # make control input non-blocking
                self.header.update_header_section(section_pos=1, text="s stop ")
                self.header.update_header_section(section_pos=2, text="w work", text_color=GRAY_COLOR)
                self.header.update_header_section(section_pos=3, text="b break", text_color=GRAY_COLOR)
                self.cmdwin._change_prompt(prompt=self.mode_properties[self.mode]["cmdwin_prompt"], centered=True)

                while True:
                    key = self.cmdwin.win.getch()
                    if key in [ord("s"), ord("w"), ord("b")]:
                        break
                    self._refresh_timer_windows()
                    self.set_seconds = self._seconds_left
                    if self.set_seconds < 1:
                        break
                    sleep(0.5)

        if self.set_seconds < 1:
            self._alarm()
            self.switch_mode()

    def _make_timer_windows(self, scn_h: int, scn_w: int) -> None:
        """Construct a border window for the timer and windows for each timer character.

        Args:
            scn_h (int): Screen height
            scn_w (int): Screen width
        """

        # Create a window for the main content
        timer_window_height = scn_h - 6
        content_width = 11 * 4 + 2 * 3 + 1  # four characters @ 11 width/ea, three spaces between, one color
        content_height = 11
        content_y_start = int((timer_window_height - content_height) / 2) + 3  # centered under header
        content_x_start = int((scn_w - content_width) / 2)

        self.timer_border_window = curses.newwin(timer_window_height, scn_w, 3, 0)
        self.timer_border_window.bkgd(curses.color_pair(GRAY_COLOR))
        self.timer_border_window.box()
        self.timer_border_window.refresh()

        self.timer_windows = {
            0: curses.newwin(10, 11, content_y_start, content_x_start),
            1: curses.newwin(10, 11, content_y_start, content_x_start + 12),
            2: curses.newwin(10, 11, content_y_start, content_x_start + 12 * 2 + 3),
            3: curses.newwin(10, 11, content_y_start, content_x_start + 12 * 3 + 3),
        }

    def switch_mode(self, new_mode: Mode = None) -> None:
        """Toggle the current mode, or switch to the provided mode. Prompts for user to input or confirm time and
            sets the timer.

        Args:
            new_mode (Mode, optional): Mode to switch to. Defaults to None.
        """
        if new_mode:
            self.mode = new_mode
        else:
            self.mode = Mode.WORK if self.mode == Mode.BREAK else Mode.BREAK

        with self.cmdwin._temp_change():
            self.cmdwin._change_prompt(f"{self.mode.value} minutes [{self.mode_properties[self.mode]['minutes']}]: ? ")
            with echo_and_cursor_on():
                try:
                    self.mode_properties[self.mode]["minutes"] = self.cmdwin._get_mins()
                except Exception:
                    pass  # no change to current settings if input is invalid

        self.set_timer(minutes=self.mode_properties[self.mode]["minutes"])


class CommandWindow:
    """Window at the bottom of the screen for command input."""

    win: curses.window
    prompt: str
    scn_w: int

    def __init__(self, scn_h: int, scn_w: int) -> None:
        self.scn_w = scn_w
        self.win = curses.newwin(3, scn_w, scn_h - 3, 0)
        self._change_prompt()

    @contextmanager
    def _temp_change(self):
        """Revert the prompt to default and turn on blocking character input on exit."""
        try:
            yield
        finally:
            self._change_prompt()  # reset prompt
            self.win.timeout(-1)  # set blocking input

    def _change_prompt(self, prompt: str = "Select option (q to quit)", centered: bool = False) -> None:
        """Change the command window prompt.

        Args:
            prompt (str, optional): Text of new prompt. Defaults to "Select option (q to quit)".
            centered (bool, optional): Center the prompt in the command window. Defaults to False.
        """
        self.prompt = prompt
        self.win.clear()
        self.win.bkgd(curses.color_pair(GRAY_COLOR))
        self.win.box()
        x = 2
        if centered:
            x = int((self.scn_w - len(prompt)) / 2)
        self.win.addstr(1, x, prompt, curses.color_pair(DEFAULT_COLOR))
        self.win.refresh()

    def _get_mins(self) -> int:
        """Allow user input to set timer minutes. Defaults to last input.

        Returns:
            int: Minutes as input by user
        """
        mins = int(self.win.getstr(1, 2 + len(self.prompt), 2).decode(encoding="utf-8"))
        if mins > 99:
            mins = 99
        elif mins < 1:
            mins = 1
        return mins


class Header:
    """Dynamically constructed visual application header with multiple sections."""

    sections: dict[int, curses.window]
    orig_options: list[tuple[str, int]]
    orig_border_color: int

    def __init__(
        self, options: list[tuple[str, int]], scn_w: int, header_height: int = 3, border_color: int = GRAY_COLOR
    ) -> None:
        """Contruct and display an app header with the provided options. Width of each box is calculated to fit on the
            screen.

        Args:
            options (list[tuple[str, int]]): Tuples of ("header option text", color_pair_identifier). The first option
                in the list should be the app title and is displayed in bold.
            scn_w (int): Screen width
            header_height (int, optional): Height of the header boxes. Defaults to 3.
            border_color (int, optional): Color pair identified for the header box borders. Defaults to GRAY_COLOR.

        Raises:
            ValueError: "Header too long for screen"
        """
        header_length = sum(len(option[0]) + 4 for option in options)
        if header_length > scn_w - 2:
            raise ValueError("Header too long for screen")

        self.orig_options = options
        self.orig_border_color = border_color

        cursor = int((scn_w - header_length) / 2) - 1
        self.sections = {}
        for i, pair in enumerate(options):
            text, _ = pair
            section_width = len(text) + 4
            section = curses.newwin(header_height, section_width, 0, cursor)
            cursor += section_width
            self.sections[i] = section

        self._restore_defaults()

    @contextmanager
    def _temp_change(self):
        """Use as a context manager to make a temporary change to the header. Restores defaults on exit."""
        try:
            yield
        finally:
            self._restore_defaults()

    def _restore_defaults(self) -> None:
        """Restore the original header."""
        for i, pair in enumerate(self._orig_options):
            text, color = pair
            self.update_header_section(
                section_pos=i,
                text=text,
                text_color=color,
                border_color=self.orig_border_color,
                a_attrs=curses.A_BOLD if i == 0 else None,
            )

    def update_header_section(
        self,
        section_pos: int,
        text: str,
        text_color: int = DEFAULT_COLOR,
        border_color: int = GRAY_COLOR,
        a_attrs: int = None,
    ) -> None:
        """Update a single header section. For best results new text should have the same length as the original text.

        Args:
            section_pos (int): Header box position (from 0)
            text (str): Replacement text
            text_color (int, optional): Defaults to DEFAULT_COLOR.
            border_color (int, optional): Defaults to GRAY_COLOR.
            a_attrs (int, optional): Additional curses.A_* attributes to merge in. Defaults to None.
        """
        section = self.sections[section_pos]
        section.clear()
        section.bkgd(curses.color_pair(border_color))
        section.box()
        attrs = curses.color_pair(text_color)
        if a_attrs:
            attrs = attrs | a_attrs
        section.addstr(1, 2, text, attrs)
        section.refresh()


def main(stdscr: curses.window):

    stdscr.refresh()

    curses.curs_set(0)

    curses.init_pair(DEFAULT_COLOR, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(WORK_COLOR, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(BREAK_COLOR, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(GRAY_COLOR, GRAY, curses.COLOR_BLACK)
    curses.init_pair(WHITE_COLOR, curses.COLOR_WHITE, curses.COLOR_WHITE)

    scn_h, scn_w = stdscr.getmaxyx()

    show_welcome_screen(message=TITLE, scn_h=scn_h, scn_w=scn_w)

    header = Header(
        [
            (TITLE, DEFAULT_COLOR),
            ("s start", DEFAULT_COLOR),
            ("w work", WORK_COLOR),
            ("b break", BREAK_COLOR),
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
    curses.wrapper(main)


if __name__ == "__main__":
    run()
