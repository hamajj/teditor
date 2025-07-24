import argparse
import curses
import sys
import discordrpc
import threading
import os

sys.stdout = open(os.devnull, 'w')

rpc = discordrpc.RPC(app_id="1398062515409256558")

class Buffer:
    def __init__(self, lines):
        self.lines = lines
 
    def __len__(self):
        return len(self.lines)

    def __getitem__(self, index):
        return self.lines[index]

    @property
    def bottom(self):
        return len(self) - 1

    def insert(self, cursor, string):
        row, col = cursor.row, cursor.col
        try:
            current = self.lines.pop(row)
        except IndexError:
            current = ''
        new = current[:col] + string + current[col:]
        self.lines.insert(row, new)

    def split(self, cursor):
        row, col = cursor.row, cursor.col
        current = self.lines.pop(row)
        self.lines.insert(row, current[:col])
        self.lines.insert(row + 1, current[col:])

    def delete(self, cursor):
        row, col = cursor.row, cursor.col
        if row > self.bottom or col > len(self[row]):
            return  # Out of bounds, do nothing
        current = self.lines[row]
        if col < len(current):
            # Delete character at col
            new = current[:col] + current[col + 1:]
            self.lines[row] = new
        elif row < self.bottom:
            # Merge with next line, even if next line is empty
            self.lines[row] = current + self.lines[row + 1]
            del self.lines[row + 1]


def clamp(x, lower, upper):
    if x < lower:
        return lower
    if x > upper:
        return upper
    return x


class Cursor:
    def __init__(self, row=0, col=0, col_hint=None):
        self.row = row
        self._col = col
        self._col_hint = col if col_hint is None else col_hint

    @property
    def col(self):
        return self._col

    @col.setter
    def col(self, col):
        self._col = col
        self._col_hint = col

    def _clamp_col(self, buffer):
        self._col = min(self._col_hint, len(buffer[self.row]))

    def up(self, buffer):
        if self.row > 0:
            self.row -= 1
            self._clamp_col(buffer)

    def down(self, buffer):
        if self.row < len(buffer) - 1:
            self.row += 1
            self._clamp_col(buffer)

    def left(self, buffer):
        if self.col > 0:
            self.col -= 1
        elif self.row > 0:
            self.row -= 1
            self.col = len(buffer[self.row])

    def right(self, buffer):
        if self.col < len(buffer[self.row]):
            self.col += 1
        elif self.row < len(buffer) - 1:
            self.row += 1
            self.col = 0


class Window:
    def __init__(self, n_rows, n_cols, row=0, col=0):
        self.n_rows = n_rows
        self.n_cols = n_cols
        self.row = row
        self.col = col

    @property
    def bottom(self):
        return self.row + self.n_rows - 1

    def up(self, cursor):
        if cursor.row == self.row - 1 and self.row > 0:
            self.row -= 1

    def down(self, buffer, cursor):
        if cursor.row == self.bottom + 1 and self.bottom < len(buffer) - 1:
            self.row += 1

    def horizontal_scroll(self, cursor, left_margin=5, right_margin=2):
        page_n_cols = self.n_cols - left_margin - right_margin
        n_pages = max((cursor.col - left_margin) // page_n_cols, 0)
        self.col = n_pages * page_n_cols

    def translate(self, cursor):
        return cursor.row - self.row, cursor.col - self.col


def left(window, buffer, cursor):
    cursor.left(buffer)
    window.up(cursor)
    window.horizontal_scroll(cursor)


def right(window, buffer, cursor):
    cursor.right(buffer)
    window.down(buffer, cursor)
    window.horizontal_scroll(cursor)

def main(stdscr):
    parser = argparse.ArgumentParser()
    parser.add_argument("filename")
    args = parser.parse_args()
    filename = ""

    def run_rpc():
        rpc.set_activity(
            state= f"working on file: {args.filename}"
            #details= f"line: {cursor.row + 1}, column: {cursor.col + 1}",
        )
        rpc.run()

    threading.Thread(target=run_rpc, daemon=True).start()

    with open(args.filename) as f:
        buffer = Buffer(f.read().splitlines())
        filename = f.name

    window = Window(curses.LINES - 1, curses.COLS - 1)
    cursor = Cursor()

    curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)

    saved = False

    while True:
        stdscr.erase()
        for row, line in enumerate(buffer[window.row:window.row + window.n_rows]):
            if row == cursor.row - window.row and window.col > 0:
                line = "Â«" + line[window.col + 1:]
            if len(line) > window.n_cols:
                line = line[:window.n_cols - 1] + "Â»"
            stdscr.addstr(row, 0, line)

        cursor_y, cursor_x = window.translate(cursor)
        if 0 <= cursor_y < window.n_rows and 0 <= cursor_x < window.n_cols:
            stdscr.attron(curses.A_REVERSE)
            line = buffer[cursor.row]
            ch = line[cursor.col] if cursor.col < len(line) else " "
            stdscr.addstr(cursor_y, cursor_x, ch)
            stdscr.attroff(curses.A_REVERSE)

        status = (
            f"<< Teditor >>    File: {filename} | Ln {cursor.row+1}, Col {cursor.col+1} | "
            "Ctrl+S: Save  Ctrl+Q: Quit"
        )
        if saved:
            status += "   file saved"
        stdscr.attron(curses.A_REVERSE)
        stdscr.addstr(window.n_rows, 0, status[:window.n_cols - 1])
        stdscr.attroff(curses.A_REVERSE)

        k = stdscr.getkey()
        saved = False
        if k == "\x11":  # Ctrl+Q
            sys.exit(0)
        elif k == "\x13":  # Ctrl+S
            with open(args.filename, "w", encoding="utf-8") as f:
                f.write("\n".join(buffer.lines))
            saved = True
            status = (
                f"<< Teditor >>    File: {filename} | Ln {cursor.row+1}, Col {cursor.col+1} | "
                "Ctrl+S: Save  Ctrl+Q: Quit      File Saved"
            )
            stdscr.attron(curses.A_REVERSE)
            stdscr.addstr(window.n_rows, 0, status[:window.n_cols])
            stdscr.attroff(curses.A_REVERSE)
            stdscr.refresh()
            curses.napms(500)
            saved = False
        elif k == "KEY_LEFT":
            left(window, buffer, cursor)
        elif k == "KEY_DOWN":
            cursor.down(buffer)
            window.down(buffer, cursor)
            window.horizontal_scroll(cursor)
        elif k == "KEY_UP":
            cursor.up(buffer)
            window.up(cursor)
            window.horizontal_scroll(cursor)
        elif k == "KEY_RIGHT":
            right(window, buffer, cursor)
        elif k == "\n":
            buffer.split(cursor)
            right(window, buffer, cursor)
        elif k in ("KEY_DC", "\x04"): # delete 
            buffer.delete(cursor)
        elif k in ("KEY_BACKSPACE", "\x7f", "\x08"): # backspace 
            if (cursor.row, cursor.col) > (0, 0):
                left(window, buffer, cursor)
                buffer.delete(cursor)
        elif k == "KEY_MOUSE":
            try:
                _, mx, my, _, mouse_state = curses.getmouse()
                # Scroll up
                if mouse_state & curses.BUTTON4_PRESSED:
                    if window.row > 0:
                        window.row -= 1
                        cursor.row = max(cursor.row - 1, 0)
                # Scroll down
                elif mouse_state & curses.BUTTON5_PRESSED:
                    if window.bottom < len(buffer) - 1:
                        window.row += 1
                        cursor.row = min(cursor.row + 1, len(buffer) - 1)
            except Exception:
                pass
        else:
            buffer.insert(cursor, k)
            for _ in k:
                right(window, buffer, cursor)


if __name__ == "__main__":
    curses.wrapper(main)