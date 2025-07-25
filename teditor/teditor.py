import argparse
import curses
import sys
import os
import pygments
from pygments.lexers import PythonLexer
from pygments.lexers.c_cpp import CLexer
from pygments.lexers.c_cpp import CppLexer
from pygments.lexers.javascript import JavascriptLexer
from pygments.lexers.css import CssLexer
from pygments.lexers.html import HtmlLexer
from pygments.lexers.markup import MarkdownLexer
from pygments.lexers.rust import RustLexer
from pygments.lexers.jvm import JavaLexer
from pygments.lexers.jvm import KotlinLexer
from pygments.lexers.dotnet import CSharpLexer
from pygments.lexers.go import GoLexer
from pygments.lexers.esoteric import BrainfuckLexer
from pygments.lexers.shell import BashLexer
from pygments.lexers.textedit import VimLexer

from pygments.token import Token
import platform

if platform.system() == "Linux":
    os.system("stty -ixon")
    
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
            return
        current = self.lines[row]
        if col < len(current):
            new = current[:col] + current[col + 1:]
            self.lines[row] = new
        elif row < self.bottom:
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

def highlight_line(line, lang):
    result = []
    if lang == 'python':
        lexer = PythonLexer()
    elif lang == 'c':
        lexer = CLexer()
    elif lang == 'javascript':
        lexer = JavascriptLexer()
    elif lang == 'css':
        lexer = CssLexer() 
    elif lang == 'html':
        lexer = HtmlLexer()
    elif lang == 'markdown':
        lexer = MarkdownLexer()
    elif lang == 'rust':    
        lexer = RustLexer()
    elif lang == 'c++':
        lexer = CppLexer()
    elif lang == 'java':
        lexer = JavaLexer()
    elif lang == 'kotlin':
        lexer = KotlinLexer()
    elif lang == 'csharp':
        lexer = CSharpLexer()
    elif lang == "go":
        lexer = GoLexer()
    elif lang == "brainfuck":
        lexer = BrainfuckLexer()
    elif lang == "bash":
        lexer = BashLexer()
    elif lang == "vim":
        lexer = VimLexer()
    else:
        lexer = None
    for token, text in pygments.lex(line, lexer):
        if token in Token.Keyword:
            color = 4  # camgobegi
        elif token in Token.String:
            color = 8    # kirmizi
        elif token in Token.Comment:
            color = 2  # yesil
        elif token in Token.Name.Builtin or token in Token.Name.Function:
            color = 3 # sari
        else:
            color = 1  # duz yazi
        result.append((text, color))
    return result

def main(stdscr):
    parser = argparse.ArgumentParser()
    parser.add_argument("filename")
    args = parser.parse_args()
    filename = ""

    try:
        with open(args.filename, "r", encoding="utf-8") as f:
            buffer = Buffer(f.read().splitlines())
            filename = os.path.basename(f.name)
    except FileNotFoundError:
        raise FileNotFoundError(f"File '{args.filename}' not found.")

    window = Window(curses.LINES - 1, curses.COLS - 1)
    cursor = Cursor()

    curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)
    curses.start_color()

    if filename.endswith(".py"):
        lang = 'python'
    elif filename.endswith(".c"):
        lang = 'c'
    elif filename.endswith(".js"):
        lang = 'javascript'
    elif filename.endswith(".css"):
        lang = 'css'
    elif filename.endswith(".html"):
        lang = 'html'
    elif filename.endswith(".md"):
        lang = 'markdown'
    elif filename.endswith(".rs"):
        lang = 'rust'
    elif filename.endswith(".cpp") or filename.endswith(".cxx") or filename.endswith(".cc"):
        lang = 'c++'
    elif filename.endswith(".java"):
        lang = 'java'
    elif filename.endswith(".kt") or filename.endswith(".kts"):
        lang = 'kotlin'
    elif filename.endswith(".cs"):
        lang = 'csharp'
    elif filename.endswith(".go"):
        lang = "go"
    elif filename.endswith(".bf"):
        lang = "brainfuck"
    elif filename.endswith(".sh"): 
        lang = "bash"
    elif filename.endswith(".vim"):
        lang = "vim"
    else:
        lang = 'none'

    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)  # beyaz
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)  # yesil
    curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK) # sari
    curses.init_pair(4, curses.COLOR_CYAN, curses.COLOR_BLACK)   # camgobegi
    curses.init_pair(5, curses.COLOR_RED, curses.COLOR_BLACK)  # kirmizi
    curses.init_pair(6, curses.COLOR_MAGENTA, curses.COLOR_BLACK)  # mor
    curses.init_color(1, int(202/255*1000), int(143/255*1000), int(118/255*1000))
    curses.init_pair(8, 1, curses.COLOR_BLACK)  # light pink on black

    saved = False

    while True:
        stdscr.erase()
        for row, line in enumerate(buffer[window.row:window.row + window.n_rows]):
            if row == cursor.row - window.row and window.col > 0:
                line = "«" + line[window.col + 1:]
            if len(line) > window.n_cols:
                line = line[:window.n_cols - 1] + "»"
            col = 0
            if lang == "none":
                text = line
                if len(text) > window.n_cols:
                    text = text[:window.n_cols]
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(row, col, text)
                stdscr.attroff(curses.color_pair(1))
            else:
                for text, color in highlight_line(line, lang):
                    if col + len(text) > window.n_cols:
                        text = text[:window.n_cols - col]
                    stdscr.attron(curses.color_pair(color))
                    stdscr.addstr(row, col, text)
                    stdscr.attroff(curses.color_pair(color))
                    col += len(text)
                    if col >= window.n_cols:
                        break

        cursor_y, cursor_x = window.translate(cursor)
        if 0 <= cursor_y < window.n_rows and 0 <= cursor_x < window.n_cols:
            stdscr.attron(curses.A_REVERSE)
            if 0 <= cursor.row < len(buffer):
                line = buffer[cursor.row]
            else:
                line = ""
            ch = line[cursor.col] if cursor.col < len(line) else " "
            stdscr.addstr(cursor_y, cursor_x, ch)
            stdscr.attroff(curses.A_REVERSE)

        status = (
            f"<< Teditor >>   File: {filename} | Ln {cursor.row+1}, Col {cursor.col+1} | "
            "Ctrl+S: Save  Ctrl+Q: Quit"
        )
        if saved:
            status += "   File Saved"
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
                f"<< Teditor >>   File: {filename} | Ln {cursor.row+1}, Col {cursor.col+1} | "
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
        elif k == "KEY_HOME":
            cursor.col = 0
            window.col = 0
        elif k == "KEY_END":
            cursor.col = len(buffer[cursor.row])
            window.col = max(0, len(buffer[cursor.row]) - window.n_cols + 1)
        elif k == "\n":
            buffer.split(cursor)
            right(window, buffer, cursor)
        elif k in ("KEY_DC", "\x04"): # delete 
            buffer.delete(cursor)
        elif k in ("KEY_BACKSPACE", "\x7f", "\x08"): # backspace 
            if (cursor.row, cursor.col) > (0, 0):
                left(window, buffer, cursor)
                buffer.delete(cursor)
        elif k == "\t":  # Tab key
            buffer.insert(cursor, "    ")
            for _ in range(4):
                right(window, buffer, cursor)
        elif k == "(":
            buffer.insert(cursor, "()")
            right(window, buffer, cursor)
        elif k == "[":
            buffer.insert(cursor, "[]")
            right(window, buffer, cursor)
        elif k == "{":
            buffer.insert(cursor, "{}")
            right(window, buffer, cursor)
        elif k == '"':
            buffer.insert(cursor, '""')
            right(window, buffer, cursor) 
        elif k == "KEY_MOUSE":
            try:
                _, mx, my, _, mouse_state = curses.getmouse()
                # yukari kaydirma
                for _ in range(4):
                    if mouse_state & curses.BUTTON4_PRESSED:
                        if window.row > 0:
                            window.row -= 1
                            cursor.row = max(cursor.row - 1, 0)
                # asagi kaydirma
                for _ in range(4):
                    if mouse_state & curses.BUTTON5_PRESSED:
                        if window.bottom < len(buffer) - 1:
                            window.row += 1
                            cursor.row = min(cursor.row + 1, len(buffer) - 1)
            except Exception:
                pass
        else:
            buffer.insert(cursor, k)
            for _ in k:
                right(window, buffer, cursor)

def cli_main():
    curses.wrapper(main)
