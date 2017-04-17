import asyncio
from .constants import *
import curses
import sys
import os
import math
import signal


class Console:
    snapshot = None
    active = False
    cmd_history = []
    cmd_history_selector = 0
    wait_command = False
    top = 0
    left = 0
    widget_heights = 0
    name = 'Console'
    start_error = []

    def __init__(self, terminal, split_height,
                 stdout_port, stderr_port, logger_port, stdin_port):
        self.stdin_port = stdin_port
        self.stderr_port = stderr_port
        self.stdout_port = stdout_port
        self.control = {"<UP>": self.cursor_up_down_esc,
                        "<SHIFT+UP>": self.scroll_up,
                        "<SHIFT+DOWN>": self.scroll_down,
                        # "<CTRL+UP>": self.resize_up,
                        # "<CTRL+DOWN>": self.resize_down,
                        "<DOWN>": self.cursor_up_down_esc,
                        "<ESC>": self.cursor_up_down_esc,
                        "<PAGEUP>": self.scroll_up,
                        "<PAGEDOWN>": self.scroll_down,
                        # "<HOME>": self.scroll_home,
                        # "<END>": self.scroll_end,
                        "<RIGHT>": self.cursor_right,
                        "<LEFT>": self.cursor_left,
                        "<ENTER>": self.cursor_enter,
                        "<BACKSPACE>": self.cursor_backspace,
                        "<DEL>": self.cursor_del}
        self.terminal = terminal
        self.width, self.height = os.get_terminal_size()
        for widget in self.terminal.widget:
            widget.height = math.floor(widget.height * (1 - split_height))
            self.widget_heights += widget.height
        self.height = self.height - self.widget_heights

    def resize(self):
        lh = self.height
        lw = self.width
        self.height = self.rh
        self.width = self.terminal.screen_width
        lh = self.height - lh
        lw = self.width - lw
        self.terminal.cursor_y += lh
        self.cursor_y = self.terminal.cursor_y
        self.terminal.cursor_x += lw
        self.top = self.widget_heights
        # self.save_cursor_x = self.terminal.cursor_x
        # self.save_cursor_y = self.terminal.cursor_y

        self.screen = self.terminal.screen.subwin(
            self.height - self.margin,
            self.width, self.top + self.header_margin,
            self.left)
        self.screen.clear()
        self.update_header()
        self.screen.bkgd(curses.color_pair(PANEL))
        self.scroll_end()
        self.pressed_key = "<reszie>"
        asyncio.async(self.cursor_up_down_esc())

        self.screen.noutrefresh()
        self.doupdate()

    def start(self):
        self.height = self.terminal.screen_height - self.widget_heights
        self.width = self.terminal.screen_width
        self.oldh = 0
        self.top = self.widget_heights
        self.header_margin = 1
        self.footer_margin = 0
        self.cursor_marker = b'\033[7m>\033[2m '
        self.margin = self.header_margin + self.footer_margin
        self.screen = self.terminal.screen.subwin(
            self.height - self.margin, self.width,
            self.top + self.header_margin, self.left)
        self.data = [b'']
        self.input_line = [[]]
        self.color_map = [PANEL]
        self.color_pair = 0
        self.wrap = True
        self.scroll = 0
        self.cursor_y = self.height - self.margin
        self.cursor_x = 0
        self.default_cursor_y = self.height - self.margin + self.top
        self.default_cursor_x = 0
        self.save_cursor_y = self.height - self.margin + self.top
        self.save_cursor_x = 0
        self.cursor_line = 0
        self.wait_stdin = False
        self.terminal.cursor_x = self.default_cursor_x
        self.terminal.cursor_y = self.default_cursor_y
        self.command_receved = asyncio.Event()
        self.update_header()
        self.screen.bkgd(curses.color_pair(PANEL))
        # self.print_data(b''.join(self.input_line[0]))
        self.screen.noutrefresh()
        self.doupdate()
        # self.stdout = socket.socket()
        # self.stdout.connect(('127.0.0.1',8888))
        # self.terminal.loop.add_reader(self.stdout, self.stdout_data_received)
        self.console_task = asyncio.async(self.console_run())
        self.stdout_data_received_task =\
            asyncio.async(self.stdout_data_received())
        self.stderr_data_received_task =\
            asyncio.async(self.stderr_data_received())
        # if self.terminal.logger is None:
        #     asyncio.async(self.logger_received())

    @asyncio.coroutine
    def logger_received(self):
        try:
            reader, writer =\
                yield from asyncio.wait_for(asyncio.open_connection('127.0.0.1', self.logger_port), 10)
        except Exception:
            self.shutdown()
            print('''Can't connect to Logger Server''')
        while True:
            try:
                data = yield from reader.readline()
                if data == b'':
                    break
                self.write(data[:-1] + b'\n')
            except Exception as err:
                pass

    def shutdown(self):
            sys.excepthook = self.terminal._excepthook
            curses.nocbreak()
            curses.echo()
            curses.endwin()
            try:
                self.terminal.loop.close()
            except Exception:
                pass
            return

    @asyncio.coroutine
    def stdout_data_received(self):
        try:
            reader, writer = yield from asyncio.wait_for (asyncio.open_connection('127.0.0.1', self.stdout_port), 10)
        except Exception:
            self.start_error.append('Cant connect to Logger Server')
        while True:
            try:
                data = yield from reader.readline()
                if data == b'':
                    break
                self.write(b'\033[5m' + data[:-1] + b'\033[2m \n')
                yield from asyncio.sleep(0.001)
            except Exception as err:
                pass

    @asyncio.coroutine
    def stderr_data_received(self):
        try:
            reader, writer = yield from asyncio.wait_for (asyncio.open_connection('127.0.0.1', self.stderr_port), 10)
        except Exception:
            self.start_error.append('Cant connect to Logger Server')
        while True:
            try:
                data = yield from reader.readline()
                if data == b'':
                    break
                self.write(b'\033[13m' + data[:-1] + b'\033[2m\n')
            except Exception as err:
                pass

    @asyncio.coroutine
    def console_run(self):
        while True:
            yield from self.set_console_input_marker()
            self.cmd_history.append([])
            self.cmd_history_selector = len(self.cmd_history) - 1
            self.wait_command = True
            command = yield from self.read()
            self.wait_command = False
            # self.cmd_history[len(self.cmd_history) - 1] = []
            # print(len(self.input_line))
            if len(self.input_line[0]) > 2:
                self.cmd_history[len(self.cmd_history) - 1] = []

                for l in self.input_line:
                    for s in l:
                        self.cmd_history[len(self.cmd_history) - 1].append(s)
            else:
                self.cmd_history.pop()

            result = yield from self.process_command(command.decode())
            if result:
                pass
                self.write(str(result).encode() + b'\n')

    @asyncio.coroutine
    def process_command(self, cmd):
        if not cmd:
            return
        cmd = cmd.rstrip()
        if cmd == 'exit' or cmd == 'quit' or cmd == 'q':
            # sys.excepthook = self.terminal._excepthook
            curses.nocbreak()
            curses.echo()
            curses.endwin()
            # yield from self.console_task.cancell()
            # yield from self.stdout_data_received_task.cancell()
            # yield from self.stderr_data_received_task.cancell()
            # for widget in self.terminal.widget:
            #    yield from widget.task.cancell()
            self.terminal.loop.stop()
            # self.terminal.loop.close()
            print('Terminal disconnected')
        if cmd == 'help':
            self.print_line('Console internal command:')
            self.print_line('')
            self.print_line('\033[9mexit\033[2m   --  exit terminal')
            self.print_line('\033[9mquit\033[2m   --  exit terminal')
            self.print_line('\033[9mkill\033[2m   --  kill daemon')
            self.print_line('')
            return
        if cmd == 'kill':
            PID_FILE = getattr(sys.modules['__main__'], 'PID_FILE')
            f = open(PID_FILE, 'r')
            print("PID_FILE %s" PID_FILE)
            i = f.read()
            f.close()
            try:
                os.kill(int(i), signal.SIGTERM)
                self.print_line('Kill command sent')
            except Exception as err:
                self.print_line('Kill command error: %s' % err)
            return
        try:
            reader, writer = yield from asyncio.wait_for(asyncio.open_connection('127.0.0.1', self.stdin_port), 10)
            writer.write(cmd.encode() + b'\n')
            writer.close()
            return None
        except Exception as err:
            return 'stdin port error%s' % err

    def print_line(self, data):
        data = str(data) + '\n'
        self.write(data.encode())

    @asyncio.coroutine
    def c_print_line(self, data):
        self.write((str(data) + '\n').encode())

    @asyncio.coroutine
    def set_console_input_marker(self):
        # last_line = len(self.data) - 1
        self.write(self.cursor_marker)
        self.doupdate()

    @asyncio.coroutine
    def read(self):
        self.input_line = [[]]
        self.cursor_line = 0
        self.wait_stdin = True
        l = self.data[len(self.data) - 1]
        self.data[len(self.data) - 1] = b''
        self.default_cursor_x = self.dst_len(l)
        p = len(l)
        self.cursor_x = self.dst_len(l)
        self.terminal.cursor_x = self.dst_len(l)
        self.doupdate()
        curses.curs_set(1)
        while l:
            esc = b''
            while True:
                escape, l = self.pop_escape_code(l)
                if escape:
                    esc += escape
                else:
                    break
            symbol, l = self.pop_symbol(l)
            symbol = esc + symbol
            esc = b''
            while True:
                escape, l = self.pop_escape_code(l)
                if escape:
                    esc += escape
                else:
                    break

            if not symbol:
                break
            self.input_line[0].append(symbol + esc)
        yield from self.command_receved.wait()
        self.command_receved.clear()
        cmd = b''
        for line in self.input_line:
            cmd += b''.join(line)
        self.write(cmd + b'\n', False)
        self.scroll_screen(1)
        self.screen.noutrefresh()
        self.doupdate()
        curses.curs_set(0)
        return cmd[p:]

    def write(self, data, display=True):
        start_line = len(self.data) - 1
        lines_added = 0
        data = self.data[len(self.data) - 1] + data
        self.data[len(self.data) - 1] = b''
        self.cursor_x = 0
        color_pair = self.color_map[len(self.data) - 1]
        while data:
            while True:
                escape, data = self.pop_escape_code(data)
                if escape:
                    if escape[-1:] == b'm' and escape[0:2] == b'\033[':
                        sequence = escape[2:-1].split(b';')
                        for i in sequence:
                            color_pair = int(i)
                    while escape:
                        self.data[len(self.data) - 1] += escape[0:1]
                        escape = escape[1:]
                    continue
                else:
                    break

            symbol, data = self.pop_symbol(data)

            if symbol:
                self.data[len(self.data) - 1] += symbol
                if symbol[0] == 10 or self.dst_len(self.data[len(self.data) - 1]) == self.width:
                    lines_added += 1
                    self.data.append(b'')
                    self.color_map.append(color_pair)
        if self.scroll:
            self.scroll += lines_added
        else:
            if display:
                if self.wait_stdin:
                    y_position = self.height - len(self.input_line)
                    if y_position > 0 and not self.scroll:
                        save_y = self.cursor_y
                        save_x = self.cursor_x
                        self.cursor_y = y_position
                        i = len(self.data) - 1
                        while True:
                            self.cursor_x = 0
                            self.screen.attron(curses.color_pair(self.color_map[i]))
                            self.print_data(self.data[i], False)
                            i -= 1
                            if i < 0:
                                break
                            self.cursor_y -= 2
                            if self.cursor_y < 0:
                                break
                        self.cursor_y = save_y
                        self.cursor_x = save_x
                        self.screen.noutrefresh()
                else:
                    # self.screen.attron(curses.color_pair(self.color_map[start_line-1]))
                    for i in range(start_line, len(self.data)):
                        self.print_data(self.data[i], False)
                    self.screen.noutrefresh()

        self.update_header()
        self.doupdate()

    @asyncio.coroutine
    def execute(self, cmd):
        pass

    def update_header(self):
        if self.active:
            color = curses.color_pair(ACTIVE_HEADER)
        else:
            color = curses.color_pair(HEADER)

        if self.scroll:
            h = 'Console: %s [%s] ' % (len(self.data) - 1, self.scroll)
        else:
            h = 'Console: %s  ' % (len(self.data) - 1)
        self.terminal.screen.move(self.top, self.left)
        self.terminal.screen.addstr(h.ljust(self.width, ' '), color)
        self.terminal.screen.noutrefresh()

    def doupdate(self):
        if self.scroll or not self.active:
            curses.curs_set(0)
        else:
            curses.curs_set(1)
        curses.setsyx(self.terminal.cursor_y, self.terminal.cursor_x)
        curses.doupdate()

    def print_data(self, data, refresh=True):
        # print data until line ended or line break or data ended

        while data:
            # if cursor 'y' position is out of screen then scroll
            if self.cursor_y == (self.height - self.margin):
                self.screen.scrollok(True)
                self.screen.scroll()
                self.screen.scrollok(False)
                self.cursor_y -= 1
            self.screen.move(self.cursor_y, self.cursor_x)
            self.screen.clrtoeol()

            while self.cursor_x < self.width and data:

                data = self.process_escape_sequences(data, True)
                if not data:
                    break
                symbol, data = self.pop_symbol(data)
                # line break
                if symbol[0] == 10:
                    self.cursor_x = self.width
                    break
                try:
                    # print symbol
                    self.screen.addstr(self.cursor_y, self.cursor_x, symbol)
                except Exception:
                    pass
                self.cursor_x += 1
                if self.cursor_x == self.width:
                    while data:
                        data = self.process_escape_sequences(data, True)
                        if not data:
                            break
                        symbol, data = self.pop_symbol(data)
                        if symbol[0] == 10:
                            break
            # end of string do line break
            if self.cursor_x == self.width:
                self.cursor_x = 0
                self.cursor_y += 1
                if symbol[0] != 10:
                    symbol, data = self.pop_symbol(data)
                    if not data and not symbol:
                        break
                    if not data:
                        data = symbol
                    else:
                        if symbol[0] != 10:
                            data = symbol + data

        if refresh:
            self.screen.noutrefresh()

    def process_escape_sequences(self, byte_line, active=False):
        sequence = b''
        while True:
            sequence, byte_line = self.pop_escape_code(byte_line)
            if sequence == b'':
                return byte_line
            if sequence[-1:] == b'm' and sequence[0:2] == b'\033[':
                sequence = sequence[2:-1].split(b';')
                for i in sequence:
                    self.color_pair = int(i)
                    k = int(i)
                    if active:
                        self.screen.attron(curses.color_pair(self.color_pair))

    def pop_escape_code(self, byte_line):
        sequence = b'\033['
        allowed_values = [b'1', b'2', b'3', b'4', b'5', b'6',
                          b'7', b'8', b'9', b'0', b';', b'm']
        if len(byte_line) < 3:
            return b'', byte_line
        if byte_line[0:2] == sequence:
            byte_line = byte_line[2:]
            while byte_line:
                if byte_line[0:1] in allowed_values:
                    sequence += byte_line[0:1]
                    byte_line = byte_line[1:]
                    if sequence[-1:] == b'm':
                        return sequence, byte_line
                else:
                    break
            return sequence, byte_line
        else:
            return b'', byte_line

    def pop_symbol(self, byte_line):
        symbol = b''
        tmp = byte_line
        count = 0
        if not byte_line:
            return None, b''
        while byte_line:
            symbol = symbol + byte_line[0:1]
            byte_line = byte_line[1:]
            try:
                symbol.decode(ENCODING)
                return symbol, byte_line
                symbol = b''
                count = 0
            except Exception:
                count += 1
                if count == 6:
                    break
        return self.pop_symbol(tmp[1:])

    @asyncio.coroutine
    def process_key(self, key):
        # print('key pressed: %s' %key)
        self.pressed_key = key
        if key in self.control:
            yield from self.control[key]()
        else:
            if len(key) < 3 and self.wait_stdin:
                yield from self.echo(key)

    @asyncio.coroutine
    def cursor_enter(self):
        self.wait_stdin = False
        self.command_receved.set()

    @asyncio.coroutine
    def scroll_up(self):
        length_data = len(self.data)
        length_command = len(self.input_line)
        if self.height - self.margin >= length_command + length_data:
            return
        if length_command + length_data - (self.height - self.margin) - self.scroll == 1:
            return
        self.scroll_screen(-1)
        self.scroll += 1
        save_x = self.cursor_x
        save_y = self.cursor_y
        self.cursor_x = 0
        self.cursor_y = 0
        if length_command >= (self.height - self.margin) + self.scroll:
            line = length_command - (self.height - self.margin) - self.scroll
            self.screen.attron(curses.color_pair(self.color_map[line]))
            self.print_data(b''.join(self.input_line[line]))
        else:
            l = length_command + length_data - (self.height - self.margin) - self.scroll - 1
            self.screen.attron(curses.color_pair(self.color_map[l]))
            self.print_data(self.data[l])
        self.cursor_x = save_x
        self.cursor_y = save_y
        self.screen.noutrefresh()
        self.doupdate()

    @asyncio.coroutine
    def scroll_down(self):
        length_data = len(self.data)
        length_command = len(self.input_line)
        if not self.scroll:
            self.screen.noutrefresh()
            return self.doupdate()
        self.scroll_screen(1)
        self.scroll -= 1
        save_x = self.cursor_x
        save_y = self.cursor_y
        self.cursor_x = 0
        self.cursor_y = (self.height - self.margin) - 1
        if length_command > self.scroll:
            line = length_command - self.scroll - 1
            self.print_data(b''.join(self.input_line[line]))
        else:
            l = length_command + length_data - self.scroll - 2
            self.print_data(self.data[l])
        self.cursor_x = save_x
        self.cursor_y = save_y
        self.screen.noutrefresh()
        self.doupdate()

    def scroll_end(self):
        self.scroll = 0
        h = 0
        while h < self.height - self.margin:
            line = len(self.input_line) - 1 - h
            if line < 0:
                break
            save_x = self.cursor_x
            save_y = self.cursor_y

            self.cursor_x = 0
            self.cursor_y = self.height - self.margin - h - 1
            # if line >= 0 and line < len(self.color_map):
            # self.screen.attron(curses.color_pair(self.color_map[line]))
            self.print_data(b''.join(self.input_line[line]))
            self.cursor_x = save_x
            self.cursor_y = save_y
            h += 1
        c = 0

        while h <= self.height - self.margin:
            line = len(self.data) - 1 - c
            if line < 0:
                break
            save_x = self.cursor_x
            save_y = self.cursor_y

            self.cursor_x = 0
            self.cursor_y = self.height - self.margin - h
            self.screen.attron(curses.color_pair(self.color_map[line]))
            self.print_data(self.data[line])

            self.cursor_x = save_x
            self.cursor_y = save_y
            h += 1
            c += 1

        self.screen.noutrefresh()
        self.doupdate()

    @asyncio.coroutine
    def cursor_up_down_esc(self):
        if self.pressed_key == '<ESC>' and self.scroll:
            return self.scroll_end()
        if not self.wait_command:
            return
        if not self.cmd_history_selector and self.pressed_key == '<UP>':
            return
        if self.cmd_history_selector == (len(self.cmd_history)-1) and self.pressed_key == '<DOWN>':
            return
        if self.pressed_key != '<ESC>':
            # save recent command
            self.cmd_history[self.cmd_history_selector] = []
            for l in self.input_line:
                for s in l:
                    self.cmd_history[self.cmd_history_selector].append(s)
        # length of previus command
        lines_prev = len(self.input_line)

        # decrease comand pointer and load
        if self.pressed_key == '<UP>':
            self.cmd_history_selector -= 1

        if self.pressed_key == '<DOWN>':
            self.cmd_history_selector += 1

        self.input_line = [[]]
        if self.pressed_key != '<ESC>':
            width = self.width
            for i in self.cmd_history[self.cmd_history_selector]:
                if not width:
                    self.input_line.append([])
                    width = self.width
                width -= 1
                self.input_line[len(self.input_line) - 1].append(i)
            if len(self.input_line[len(self.input_line) - 1]) == self.width:
                self.input_line.append([])
        else:
            l = self.cursor_marker
            while l:
                esc = b''
                while True:
                    escape, l = self.pop_escape_code(l)
                    if escape:
                        esc += escape
                    else:
                        break
                symbol, l = self.pop_symbol(l)
                symbol = esc + symbol
                esc = b''
                while True:
                    escape, l = self.pop_escape_code(l)
                    if escape:
                        esc += escape
                    else:
                        break
                if not symbol:
                    break
                self.input_line[0].append(symbol + esc)

        lines = len(self.input_line)
        self.cursor_line = len(self.input_line) - 1
        lines_change = lines_prev - lines
        self.screen.attron(curses.color_pair(PANEL))
        # при значении больше ноля мы должны отскролить экран сверху вниз
        if lines_change:
            if lines_change > self.height - self.margin:
                lines_change = self.height - self.margin

            self.scroll_screen(-1 * lines_change)
            save_x = self.cursor_x
            save_y = self.cursor_y

            for i in range(lines_change):
                self.cursor_x = 0
                self.cursor_y = i
                line = len(self.data) - 1 - ((self.height - self.margin) - len(self.input_line)) + i
                if line >= 0:

                    self.print_data(self.data[line])

            self.cursor_x = save_x
            self.cursor_y = save_y

        self.terminal.cursor_x = len(self.input_line[len(self.input_line) - 1])

        h = 0
        while h < self.height - self.margin:
            line = len(self.input_line) - 1 - h
            if line < 0:
                break
            # save_x = self.cursor_x
            # save_y = self.cursor_y

            self.cursor_x = 0
            self.cursor_y = self.height - self.margin - h - 1
            self.print_data(b''.join(self.input_line[line]))

            # self.cursor_x = save_x
            # self.cursor_y = save_y
            h += 1

        # self.screen.clear()
        self.screen.attron(curses.color_pair(self.color_pair))
        self.screen.noutrefresh()
        self.doupdate()

    @asyncio.coroutine
    def cursor_down(self):
        if not self.wait_command:
            return
        # print('cursor down')
        if self.cmd_history_selector == len(self.cmd_history) - 1:
            # print('no more history')
            return

        # save recent command
        self.cmd_history[self.cmd_history_selector] = []
        for l in self.input_line:
            for s in l:
                self.cmd_history[self.cmd_history_selector].append(s)
        # lines_prev = len(self.input_line)

    @asyncio.coroutine
    def cursor_right(self):
        if self.terminal.cursor_x < len(self.input_line[self.cursor_line]) - 1:
            self.terminal.cursor_x += 1
        else:
            if self.cursor_line < len(self.input_line) - 1:
                if self.terminal.cursor_y < self.top + self.height - self.margin:
                    self.terminal.cursor_x = 0
                    self.terminal.cursor_y += 1
                    self.cursor_line += 1
                else:
                    self.scroll_screen(1)
                    self.cursor_line += 1
                    self.terminal.cursor_x = 0
                    self.cursor_y = self.height - self.margin - 1
                    self.cursor_x = 0
                    l = b''.join(self.input_line[self.cursor_line])
                    self.print_data(l)
            else:
                if self.terminal.cursor_x < len(self.input_line[self.cursor_line]):
                    self.terminal.cursor_x += 1
        self.doupdate()

    @asyncio.coroutine
    def cursor_left(self):
        # событие по скролингу обратно
        if not self.terminal.cursor_y > (self.top + 1) and self.terminal.cursor_x == 0:
            self.scroll_screen(-1)
            self.cursor_line -= 1
            self.screen.noutrefresh()
            self.cursor_y = 0
            self.cursor_x = 0
            l = b''.join(self.input_line[self.cursor_line])
            self.print_data(l)
            self.terminal.cursor_x = self.width - 1
            return self.doupdate()

        if self.terminal.cursor_x < self.default_cursor_x + 1 and self.cursor_line == 0:
            return
        if self.terminal.cursor_x == 0:
            self.cursor_line -= 1
            self.terminal.cursor_x = self.width
            self.terminal.cursor_y -= 1

        self.terminal.cursor_x -= 1
        self.doupdate()

    @asyncio.coroutine
    def cursor_del(self):
        line = self.cursor_line
        # position = self.terminal.cursor_x
        total_lines = len(self.input_line)
        last_line = total_lines - 1
        if line == last_line and self.terminal.cursor_x == len(self.input_line[line]):
            return
        if self.terminal.cursor_x == self.width:
            # if not line:
            #     return
            self.cursor_line += 1
            self.terminal.cursor_x = 0
            self.terminal.cursor_y += 1

        self.terminal.cursor_x += 1
        yield from self.cursor_backspace()

    @asyncio.coroutine
    def cursor_backspace(self):
        line = self.cursor_line
        position = self.terminal.cursor_x
        # total_lines = len(self.input_line)
        # last_line = total_lines - 1
        if not line and position < self.default_cursor_x + 1:
            return
        if not position:
            position = self.width
            self.terminal.cursor_x = self.width
            self.terminal.cursor_y -= 1
            del self.input_line[line - 1][position - 1]
            line -= 1
            self.cursor_line -= 1
            if self.terminal.cursor_y == (self.top + self.header_margin - 1):
                self.terminal.cursor_x = 1
                self.terminal.cursor_y += 1
                self.cursor_line += 1
                line += 1
                self.input_line[line - 1].append(self.input_line[line].pop(0))
        else:
            del self.input_line[line][position - 1]
        self.terminal.cursor_x -= 1
        t = line
        while t < len(self.input_line):
            if t == len(self.input_line) - 1:
                break
            if len(self.input_line[t]) == self.width - 1:
                if self.input_line[t + 1]:
                    self.input_line[t].append(self.input_line[t+1].pop(0))
                else:
                    del self.input_line[t + 1]
                    self.scroll_screen(-1)
                    str_number = len(self.data) - self.height + len(self.input_line)
                    save_x = self.cursor_x
                    save_y = self.cursor_y
                    self.cursor_x = 0
                    self.cursor_y = 0
                    self.print_data(self.data[str_number])
                    self.cursor_x = save_x
                    self.cursor_y = save_y
                    self.terminal.cursor_y += 1
            else:
                break
            t += 1
        t_line = len(self.input_line) - 1
        x = 0

        while True:
            l = b''.join(self.input_line[t_line])
            if not l:
                l = b' '
            self.cursor_y = self.height - self.margin - 1 - x
            self.cursor_x = 0
            self.print_data(l, False)
            t_line -= 1
            x += 1
            if x == self.height - self.margin or x > len(self.input_line) - 1:
                break

        self.screen.noutrefresh()
        self.doupdate()

    @asyncio.coroutine
    def echo(self, key):
        if self.scroll:
            self.scroll_end()
        self.screen.attron(curses.color_pair(PANEL))
        key, rest = self.pop_symbol(key.encode())
        line = self.cursor_line
        total_lines = len(self.input_line)
        last_line = total_lines - 1
        position = self.terminal.cursor_x
        if line == last_line and position == len(self.input_line[line]):
            self.input_line[line].append(key)
            self.cursor_y = self.height-self.margin - 1
            self.cursor_x = self.terminal.cursor_x
            self.terminal.cursor_x += 1
            self.print_data(key, False)
            if self.terminal.cursor_x == self.width:
                self.input_line.append([])
                self.terminal.cursor_x = 0
                self.scroll_screen(1)
                self.cursor_line += 1
        else:
            self.input_line[line].insert(position, key)
            t = line
            while True:
                if len(self.input_line[t]) > self.width:
                    key = self.input_line[t].pop()
                else:
                    break
                if t == len(self.input_line) - 1:
                    self.input_line.append([key])
                    self.scroll_screen(1)
                    self.terminal.cursor_y -= 1
                    break
                self.input_line[t + 1].insert(0, key)
                t += 1

            t_line = len(self.input_line) - 1
            x = 0
            while True:
                l = b''.join(self.input_line[t_line])
                self.cursor_y = self.height - self.margin - 1 - x
                self.cursor_x = 0
                self.print_data(l, False)
                t_line -= 1
                x += 1
                if t_line < self.cursor_line:
                    break

            if self.terminal.cursor_x >= self.width - 1:
                self.terminal.cursor_x = 0
                self.terminal.cursor_y += 1
                self.cursor_line += 1
            else:
                self.terminal.cursor_x += 1
        self.screen.attron(curses.color_pair(self.color_pair))
        self.screen.noutrefresh()
        self.doupdate()

    def dst_len(self, byte_line):
        count = 0
        while byte_line:
            byte_line = self.process_escape_sequences(byte_line)
            symbol, byte_line = self.pop_symbol(byte_line)
            if not symbol:
                break
            count += 1
        return count

    def scroll_screen(self, n):
        self.screen.scrollok(True)
        self.screen.scroll(n)
        self.screen.scrollok(False)

    @asyncio.coroutine
    def set_inactive(self):
        self.active = False
        self.save_cursor_x = self.terminal.cursor_x
        self.save_cursor_y = self.terminal.cursor_y
        curses.curs_set(0)
        self.update_header()
        self.doupdate()

    @asyncio.coroutine
    def set_active(self):
        self.terminal.cursor_x = self.save_cursor_x
        self.terminal.cursor_y = self.save_cursor_y
        self.active = True
        curses.curs_set(1)
        self.update_header()
        self.doupdate()
