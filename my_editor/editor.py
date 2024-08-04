import curses
from enum import StrEnum


class State(StrEnum):
    INSERT = "INSERT"
    NORMAL = "NORMAL"
    COMMAND = "COMMAND"
    VISUAL = "VISUAL"
    BLOCK_VISUAL = "BLOCK_VISUAL"
    LINE_VISUAL = "LINE_VISUAL"


class Editor:
    def __init__(self, window: curses.window):
        self._col = 0
        self._line = 0
        self._window = window
        self._buf: list[str] = [""]
        self._state: State = State.INSERT
        self._state_window = self._window.subwin(curses.LINES - 1, 0)
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
        curses.init_pair(2, curses.COLOR_WHITE, 238)

        self._state_window.bkgd(" ", curses.color_pair(1))
        self._window.resize
        self._state_window.refresh()
        curses.set_escdelay(50)

    def _refresh(self):
        self._window.move(self._line, self._col)
        if self._state == State.INSERT:
            curses.curs_set(1)
        else:
            curses.curs_set(2)
        self._state_window.erase()
        self._state_window.insstr(0, 0, self._state)
        self._state_window.refresh()

    def _handle_backspace(self):
        if self._col > 0:
            self._window.delch(self._line, self._col - 1)
            self._col -= 1
        else:
            if self._line > 0:
                self._line -= 1
                self._refresh()
                self._window.clrtoeol()

    def handle_key_insert(self, key: int | str):
        match key:
            case key if isinstance(key, str) and key.isprintable():
                self._add_char_to_buf(key)
                self._window.insstr(self._line, self._col, key)
                self._col += 1
            case "\x7f":
                self._handle_backspace()
            case "\x0a":
                self._line += 1
                self._buf.insert(self._line + 1, "")
                self._col = 0
                self._hard_refresh()
            case "\x1b":
                self._state = State.NORMAL
            case curses.KEY_LEFT | curses.KEY_RIGHT | curses.KEY_UP | curses.KEY_DOWN:
                self._move_cursor(key)
            case int():
                raise ValueError(f"Got int of value {key:}")
            case _:
                raise ValueError(f" Got key {key:}with ord {ord(key):}")

    def handle_key_else(self, key):
        match key:
            case "i":
                self._state = State.INSERT
            case "I":
                self._state = State.INSERT
                self._col = 0
            case "s":
                self._window.delch(self._line, self._col)
                self._state = State.INSERT
            case (
                curses.KEY_LEFT
                | curses.KEY_RIGHT
                | curses.KEY_UP
                | curses.KEY_DOWN
                | "h"
                | "j"
                | "k"
                | "l"
            ):
                self._move_cursor(key)
            case "v":
                if self._state == State.VISUAL:
                    self._state = State.NORMAL
                else:
                    self._state = State.VISUAL
                    self._visual_start = self._visual_end = (self._line, self._col)
            case "V":
                if self._state == State.LINE_VISUAL:
                    self._state = State.NORMAL
                else:
                    self._state = State.LINE_VISUAL
                    self._visual_start = self._visual_end = (self._line, self._col)
                    for i in range(0, curses.getsyx()[1]):
                        self._window.chgat(self._line, i, curses.color_pair(2))

    def main_loop(self):
        while True:
            self._refresh()
            key = self._window.get_wch()
            match self._state:
                case State.INSERT:
                    self.handle_key_insert(key)
                case State.COMMAND:
                    self.handle_key_command(key)
                case _:
                    self.handle_key_else(key)

    def _move_cursor(self, key):
        match key:
            case curses.KEY_DOWN | "j":
                self._line += 1
            case curses.KEY_UP | "k":
                self._line -= 1
            case curses.KEY_RIGHT | "l":
                self._col += 1
            case curses.KEY_LEFT | "h":
                self._col -= 1

    def _add_char_to_buf(self, key):
        self._buf[self._line] = (
            self._buf[self._line][: self._col]
            + key
            + self._buf[self._line][self._col + 1 :]
        )

    def _hard_refresh(self):
        self._window.insstr(0, 0, "\n".join(self._buf))


def main(stdscr: curses.window):
    return Editor(stdscr).main_loop()


if __name__ == "__main__":
    print("Staring curses screen")
    exit(curses.wrapper(main))
