"""Text User Interface classes and functions."""

from __future__ import annotations

import curses
import os
import sys
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from enum import Enum
from time import sleep
from typing import TYPE_CHECKING

from . import colors
from .ascii_numbers import ASCII_NUM

if TYPE_CHECKING:
    from collections.abc import Generator

TITLE = "tomodoro."
MAX_MINS = 99


@contextmanager
def echo_and_cursor_on() -> Generator[None]:
    """Within the context manager, turn on echoing of input to the screen and a blinking cursor."""
    try:
        curses.echo()
        curses.curs_set(1)
        yield
    finally:
        curses.noecho()
        curses.curs_set(0)


def show_welcome_screen(message: str, scn_h: int, scn_w: int, speed: float = 0.15, final_sleep: float = 1.0) -> None:
    """Display a blank screen and type out the given message character by character with the given time in-between.

    Args:
        message (str): App title
        scn_h (int): Screen height
        scn_w (int): Screen width
        speed (float, optional): Seconds to sleep between printing each character to the screen. Defaults to 0.15.
        final_sleep (float, optional): Seconds to sleep after the entire message has been printed. Defaults to 1.0.

    """
    curses.curs_set(1)  # show a blinking cursor after the message for the cua
    welcome_screen = curses.newwin(1, len(message) + 1, int(scn_h / 2), int(scn_w / 2) - int(len(message) / 2))
    for char in message:
        welcome_screen.addch(char, curses.color_pair(colors.DEFAULT_COLOR) | curses.A_BOLD)
        sleep(speed)
        welcome_screen.refresh()
    sleep(final_sleep)
    curses.curs_set(0)
    del welcome_screen


class Mode(Enum):
    """Timer modes."""

    BREAK = "Break"
    WORK = "Work"


class Timer:
    """Main timer window including the character windows contained in it."""

    _scn_h: int
    _scn_w: int
    _mode: Mode
    _mode_properties: dict[Mode, dict[str, int]]
    _end_time: datetime
    _set_seconds: int
    _last_displayed_time_str: str
    _cmdwin: CommandWindow
    _header: Header
    _timer_border_window: curses.window
    _timer_windows: dict[int, curses.window]

    @staticmethod
    def _pad(num: str) -> str:
        """Pad a single digit string with a leading zero.

        Args:
            num (str): Digit to pad

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
        return curses.color_pair(self._mode_properties[self._mode]["color"])

    @property
    def _seconds_left(self) -> int:
        """Seconds between now and the timer's end time.

        Returns:
            int: Seconds

        """
        return (self._end_time - datetime.now(tz=UTC)).seconds

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
        """Get the position numbers of the displayed timer windows that need to be updated to show the new current time.

        Prevents all four timer number positions from being updated every second.

        Returns:
            list[int]: Timer window position numbers needing refresh

        """
        char_pos_changed = []
        current_timer_str = self._timer_str
        for i, last_char in enumerate(self._last_displayed_time_str):
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
        break_color: int = colors.BREAK_COLOR,
        work_color: int = colors.WORK_COLOR,
    ) -> None:
        """Instantiate.

        Args:
            cmdwin (CommandWindow): Instantiated CommandWindow object
            header (Header): Instantiated Header object
            scn_h (int): Screen height as returned by stdscr.getmaxyx()
            scn_w (int): Screen width as returned by stdscr.getmaxyx()
            work_minutes (int, optional): Initial work timer length. Defaults to 25.
            break_minutes (int, optional): Initial break timer length. Defaults to 5.
            work_color (int, optional): Work timer curses color pair identifier. Must have already set up with
                curses.init_pair. Defaults to WORK_COLOR.
            break_color (int, optional): Break timer curses color pair identifier. Must have already set up with
                curses.init_pair. Defaults to BREAK_COLOR.

        """
        self._scn_h = scn_h
        self._scn_w = scn_w
        self._cmdwin = cmdwin
        self._header = header
        self._mode = Mode.WORK
        self._mode_properties = {
            Mode.BREAK: {"minutes": break_minutes, "color": break_color, "cmdwin_prompt": "On break..."},
            Mode.WORK: {"minutes": work_minutes, "color": work_color, "cmdwin_prompt": "Working..."},
        }

        self._make_timer_windows(scn_h=scn_h, scn_w=scn_w)
        self.set_timer(minutes=work_minutes, start=False)
        self._refresh_timer_windows(initial=True)

    def _refresh_timer_windows(self, *, initial: bool = False) -> None:
        """Update timer character windows to reflect the current time left.

        Updates only windows where the character needs to change.

        Args:
            initial (bool, optional): Set True if setting all four characters for the first time. Defaults to False.

        """
        pos_changed = [0, 1, 2, 3] if initial else self._char_pos_changed()
        for update_char_pos in pos_changed:
            win = self._timer_windows[update_char_pos]
            win.addstr(0, 0, ASCII_NUM[int(self._timer_str[update_char_pos])], self._mode_color_pair)
            win.refresh()
        self._last_displayed_time_str = self._timer_str

    def set_timer(self, minutes: int, *, start: bool) -> int | None:
        """Set the timer to given number of minutes and refresh the timer display.

        Args:
            minutes (int): To set on the timer.
            start (bool): Immediately start the timer.

        Returns:
            int | None: Propagates from self.start_timer_loop(), if called.

        """
        self._set_seconds = minutes * 60 + 1  # prevent rounding down displayed value due to integer math
        self._end_time = datetime.now(tz=UTC) + timedelta(seconds=self._set_seconds)
        self._refresh_timer_windows(initial=True)
        if start:
            return self.start_timer_loop()
        return None

    def _alarm(self) -> None:
        """Alert used to indicate timer has reached zero."""
        for _ in range(5):
            os.write(1, b"\a")  # beep
            sys.stdout.flush()
            sleep(0.3)
        # TODO: - implement flashing screen

    def start_timer_loop(self) -> int | None:
        """Start the timer countdown loop.

        Temporary changes made to visual display while loop runs.

        Returns:
            int | None: If the timer loop is stopped, returns an int corresponding to ord(key_pressed).
                If the loop ends naturally, returns None.

        """
        self.start_time = datetime.now(tz=UTC)
        self._end_time = self.start_time + timedelta(seconds=self._set_seconds)

        with self._cmdwin.temp_change(), self._header.temp_change():
            self._cmdwin.win.timeout(0)  # make control input non-blocking
            self._header.update_header_section(section_pos=1, text="s stop ")
            self._header.update_header_section(section_pos=2, text="w work", text_color=colors.GRAY_COLOR)
            self._header.update_header_section(section_pos=3, text="b break", text_color=colors.GRAY_COLOR)
            self._cmdwin.change_prompt(prompt=self._mode_properties[self._mode]["cmdwin_prompt"], centered=True)

            while True:
                key = self._cmdwin.win.getch()
                if key in [ord("s"), ord("w"), ord("b")]:
                    return key
                self._refresh_timer_windows()
                self._set_seconds = self._seconds_left
                if self._set_seconds < 1:
                    break
                sleep(0.5)

        if self._set_seconds < 1:
            self._alarm()
            self.switch_mode(start=True)
        return None

    def _make_timer_windows(self, scn_h: int, scn_w: int) -> None:
        """Construct a border window for the timer and windows for each timer character.

        Args:
            scn_h (int): Screen height as returned by stdscr.getmaxyx()
            scn_w (int): Screen width as returned by stdscr.getmaxyx()

        """
        # Create a window for the main content
        timer_window_height = scn_h - 6
        content_width = 11 * 4 + 2 * 3 + 1  # four characters @ 11 width/ea, three spaces between, one color
        content_height = 11
        content_y_start = int((timer_window_height - content_height) / 2) + 3  # centered under header
        content_x_start = int((scn_w - content_width) / 2)

        self._timer_border_window = curses.newwin(timer_window_height, scn_w, 3, 0)
        self._timer_border_window.bkgd(curses.color_pair(colors.GRAY_COLOR))
        self._timer_border_window.box()
        self._timer_border_window.refresh()

        self._timer_windows = {
            0: curses.newwin(10, 11, content_y_start, content_x_start),
            1: curses.newwin(10, 11, content_y_start, content_x_start + 12),
            2: curses.newwin(10, 11, content_y_start, content_x_start + 12 * 2 + 3),
            3: curses.newwin(10, 11, content_y_start, content_x_start + 12 * 3 + 3),
        }

    def switch_mode(self, *, start: bool, new_mode: Mode = None) -> int | None:
        """Toggle the current mode or switch to the provided mode.

        Prompts for user to input or confirm time and sets the timer.

        Args:
            start (bool): Start the timer too.
            new_mode (Mode, optional): Mode to switch to. Defaults to None.

        Returns:
            int | None: Propagates from self.start_timer_loop(), if called.

        """
        if new_mode:
            self._mode = new_mode
        else:
            self._mode = Mode.WORK if self._mode == Mode.BREAK else Mode.BREAK

        with self._cmdwin.temp_change():
            self._cmdwin.change_prompt(
                f"{self._mode.value} minutes [{self._mode_properties[self._mode]['minutes']}]: ? ",
            )
            with echo_and_cursor_on():
                try:  # noqa: SIM105
                    self._mode_properties[self._mode]["minutes"] = self._cmdwin.get_mins()
                except ValueError:
                    pass  # no change to current settings if input is invalid

        return self.set_timer(minutes=self._mode_properties[self._mode]["minutes"], start=start)


class CommandWindow:
    """Window at the bottom of the screen for command input."""

    win: curses.window
    prompt: str
    scn_w: int

    def __init__(self, scn_h: int, scn_w: int) -> None:
        """Instantiate.

        Args:
            scn_h (int): Screen height as returned by stdscr.getmaxyx()
            scn_w (int): Screen width as returned by stdscr.getmaxyx()

        """
        self.scn_w = scn_w
        self.win = curses.newwin(3, scn_w, scn_h - 3, 0)
        self.change_prompt()

    @contextmanager
    def temp_change(self) -> Generator[None]:
        """Revert the prompt to default and turn on blocking character input on exit."""
        try:
            yield
        finally:
            self.change_prompt()  # reset prompt
            self.win.timeout(-1)  # set blocking input

    def change_prompt(self, prompt: str = "Select option (q to quit)", *, centered: bool = False) -> None:
        """Change the command window prompt.

        Args:
            prompt (str, optional): Text of new prompt. Defaults to "Select option (q to quit)".
            centered (bool, optional): Center the prompt in the command window. Defaults to False.

        """
        self.prompt = prompt
        self.win.clear()
        self.win.bkgd(curses.color_pair(colors.GRAY_COLOR))
        self.win.box()
        x = 2
        if centered:
            x = int((self.scn_w - len(prompt)) / 2)
        self.win.addstr(1, x, prompt, curses.color_pair(colors.DEFAULT_COLOR))
        self.win.refresh()

    def get_mins(self) -> int:
        """Allow user input to set timer minutes. Defaults to last input.

        Returns:
            int: Minutes as input by user

        """
        try:
            mins = int(self.win.getstr(1, 2 + len(self.prompt), 2).decode(encoding="utf-8"))
        except Exception as exc:
            raise ValueError("Invalid value for minutes.") from exc
        if mins > MAX_MINS:
            mins = MAX_MINS
        elif mins < 1:
            mins = 1
        return mins


class Header:
    """Dynamically constructed visual application header with multiple sections."""

    _sections: dict[int, curses.window]
    _orig_options: list[tuple[str, int]]
    _orig_border_color: int

    def __init__(
        self,
        options: list[tuple[str, int]],
        scn_w: int,
        header_height: int = 3,
        border_color: int = colors.GRAY_COLOR,
    ) -> None:
        """Contruct and display an app header with the provided options.

        Width of each box is calculated to fit on the screen.

        Args:
            options (list[tuple[str, int]]): Tuples of ("header option text", color_pair_identifier). The first option
                in the list should be the app title and is displayed in bold.
            scn_w (int): Screen width
            header_height (int, optional): Height of the header boxes. Defaults to 3.
            border_color (int, optional): Color pair identified for the header box borders. Defaults to GRAY_COLOR.

        Raises:
            ValueError: Header too long for screen

        """
        header_length = sum(len(option[0]) + 4 for option in options)
        if header_length > scn_w - 2:
            raise ValueError("Header too long for screen")

        self._orig_options = options
        self._orig_border_color = border_color

        cursor = int((scn_w - header_length) / 2) - 1
        self._sections = {}
        for i, pair in enumerate(options):
            text, _ = pair
            section_width = len(text) + 4
            section = curses.newwin(header_height, section_width, 0, cursor)
            cursor += section_width
            self._sections[i] = section

        self._restore_defaults()

    @contextmanager
    def temp_change(self) -> Generator[None]:
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
                border_color=self._orig_border_color,
                a_attrs=curses.A_BOLD if i == 0 else None,
            )

    def update_header_section(
        self,
        section_pos: int,
        text: str,
        text_color: int = colors.DEFAULT_COLOR,
        border_color: int = colors.GRAY_COLOR,
        a_attrs: int | None = None,
    ) -> None:
        """Update a single header section. For best results new text should have the same length as the original text.

        Args:
            section_pos (int): Header box position (from 0)
            text (str): Replacement text
            text_color (int, optional): Defaults to DEFAULT_COLOR.
            border_color (int, optional): Defaults to GRAY_COLOR.
            a_attrs (int, optional): Additional curses.A_* attributes to merge in. Defaults to None.

        """
        section = self._sections[section_pos]
        section.clear()
        section.bkgd(curses.color_pair(border_color))
        section.box()
        attrs = curses.color_pair(text_color)
        if a_attrs:
            attrs = attrs | a_attrs
        section.addstr(1, 2, text, attrs)
        section.refresh()
