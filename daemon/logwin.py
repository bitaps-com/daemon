import asyncio
import curses
import os
import math

from .constants import *

class LogWin:
    display_limit = 1000
    top = 0
    left = 0
    active = False
    screen_lock = False
    widget_heights = 0
    task = None

    def __init__(self, terminal):
        self.width, self.height = os.get_terminal_size()
        self.terminal = terminal
        for widget in self.terminal.widget:
            widget.height = math.floor(widget.height * (1 - 0.5))
            self.widget_heights += widget.height
        self.height = self.height - self.widget_heights
        self.control = {
            '<UP>': self.scroll_up,
            '<DOWN>': self.scroll_down,
            '<PAGEUP>': self.scroll_page_up,
            '<PAGEDOWN>': self.scroll_page_down,
            '<HOME>': self.scroll_home,
            '<END>': self.scroll_end,
        }


    def resize(self):
        lh = self.height
        lw = self.width
        self.height =  self.rh
        self.width = self.terminal.screen_width
        lh = self.height - lh
        lw = self.width -lw
        self.terminal.cursor_y+= lh
        self.cursor_y=self.terminal.cursor_y
        self.screen = self.terminal.screen.subwin(
            self.height - self.margin, self.width, self.top + self.header_margin, self.left)
        self.screen.clear()
        self.update_header()
        self.screen.bkgd(curses.color_pair(PANEL))
        self.cursor_y = 0
        self.cursor_x = 0
        s = len(self.data) - self.height - self.margin
        if s<0:
            s = 0
        for i in range(s, len(self.data)):
            self.print_data(self.data[i])


        self.screen.noutrefresh()
        self.doupdate()


    def start(self):
        self.loading = False
        self.header_margin = 1
        self.footer_margin = 0
        self.margin = self.header_margin + self.footer_margin
        self.screen = curses.newwin(self.height-self.margin, self.width,
        self.top+self.header_margin, self.left)
        self.data = [b'']
        self.color_map = [PANEL]
        self.color_pair = PANEL
        self.wrap = True
        self.scroll = 0
        self.cursor_y = 0
        self.cursor_x = 0
        self.screen.bkgd(curses.color_pair(PANEL))
        self.update_header()
        self.screen.noutrefresh()
        self.doupdate()
        curses.curs_set(0)
        self.task = asyncio.async(self.logger_received())


    @asyncio.coroutine
    def logger_received(self):

        reader, writer = yield from asyncio.wait_for (asyncio.open_connection('127.0.0.1', LOGGER_PORT), 10)
        while True:
            try:
                data = yield from reader.readline()
                if data==b'':
                    break   
                self.push_data(data)
                yield from asyncio.sleep(0.001)

            except Exception as err:
               pass




    @asyncio.coroutine
    def process_key(self, key):
        if self.loading:
            return
        if key in self.control:
            yield from self.control[key]()
            self.update_header()
            self.doupdate()

    @asyncio.coroutine
    def scroll_up(self):
        if len(self.data) <= (self.height - self.margin):
            return None
        if (len(self.data) - self.scroll - self.margin - 1 - self.height) < 0:
            return None
        self.scroll_screen(-1)
        self.cursor_y = 0
        self.cursor_x = 0
        self.scroll += 1
        self.screen.attron(curses.color_pair(
            self.color_map[len(self.data) - self.scroll - 1 - self.height]))
        self.print_data(self.data[len(self.data)-self.scroll-1 - self.height])

    @asyncio.coroutine
    def scroll_down(self):
        if not self.scroll:
            return None
        self.scroll_screen(1)
        self.scroll -= 1
        self.cursor_y = self.height-self.header_margin - 1
        self.cursor_x = 0
        self.screen.attron(curses.color_pair(self.color_map[len(self.data)-self.scroll-2]))
        self.print_data(self.data[len(self.data)-self.scroll-2])

    @asyncio.coroutine
    def scroll_page_up(self):
        for i in range(self.height - self.margin):
            yield from self.scroll_up()

    @asyncio.coroutine
    def scroll_page_down(self):
        for i in range(self.height - self.margin):
            yield from self.scroll_down()

    @asyncio.coroutine
    def scroll_home(self):
        if len(self.data) <= (self.height - self.margin):
            return None
        self.screen.clear()
        self.scroll = len(self.data) - self.margin - self.height
        self.cursor_y = 0
        self.cursor_x = 0
        for i in range(self.height - self.margin):
            self.print_data(self.data[i])

    @asyncio.coroutine
    def scroll_end(self):
        if not self.scroll:
            return None
        self.screen.clear()
        self.scroll = 0
        self.cursor_y = 0
        self.cursor_x = 0
        for i in range(len(self.data) - self.height - self.margin, len(self.data)):
            self.print_data(self.data[i])

    def scroll_screen(self, n):
        self.screen.scrollok(True)
        self.screen.scroll(n)
        self.screen.scrollok(False)




    def update_header(self):
        if self.active:
            color = curses.color_pair(ACTIVE_HEADER)
        else:
            color = curses.color_pair(HEADER)

        if self.scroll:
            h = 'Logger: %s [%s]' % (len(self.data)-1, self.scroll)
        else:
            h = 'Logger: %s ' % (len(self.data)-1)
        if self.loading:
            h += '...'


        self.terminal.screen.move(self.top, self.left)
        self.terminal.screen.addstr(h.ljust(self.width, ' '), color)
        self.terminal.screen.noutrefresh()

    def doupdate(self):
        curses.setsyx(self.terminal.cursor_y, self.terminal.cursor_x)
        curses.doupdate()

    def push_data(self, data):
        start_line = len(self.data) - 1
        lines_added = 0
        data = self.data[len(self.data)-1] + data
        self.data[len(self.data)-1] = b''
        self.cursor_x = 0

        while data:
            symbol, data = self.pop_symbol(data)
            self.data[len(self.data)-1] += symbol
            if symbol[0] == 10 or self.dst_len(self.data[len(self.data)-1]) == self.width:
                lines_added += 1
                self.data.append(b'')
                self.color_map.append(self.color_pair)

        if self.scroll:
            self.scroll += lines_added
        else:
            self.screen.attron(curses.color_pair(self.color_map[start_line]))
            for i in range(start_line, len(self.data)):
                self.print_data(self.data[i], False)
            self.screen.noutrefresh()
        while len(self.data)>self.display_limit:
            self.data.pop(0)
        self.update_header()
        self.doupdate()

    def load_data_line(self, data):
        if not data:
            return b''
        fbr = False
        self.data[0] = b''
        while data:
            symbol, data = self.rise_symbol(data)
            self.data[0] = symbol + self.data[0]
            if symbol[0] == 10 and not fbr:
                fbr = True
                continue

            if symbol[0] == 10 or self.dst_len(self.data[len(self.data)-1]) == self.width:
                if symbol[0] == 10:
                    data += self.data[0][:1]
                    self.data[0] = self.data[0][1:]
                self.data.insert(0, b'')
                self.color_map.insert(0, self.color_pair)
                return data

    @asyncio.coroutine
    def load_data(self, data):
        while data:
            for i in range(20):
                data = self.load_data_line(data)
            self.update_header()
            self.screen.noutrefresh()
            self.doupdate()
            yield from asyncio.sleep(0)
        self.loading = False
        self.update_header()
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
                    if active:
                        self.screen.attron(curses.color_pair(self.color_pair))
        # return byte_line

    def pop_escape_code(self, byte_line):
        # return b'', byte_line
        sequence = b'\033['
        allowed_values = [b'1', b'2', b'3', b'4', b'5', b'6', b'7', b'8', b'9', b'0', b';', b'm']

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
            except:
                count += 1
                if count == 6:
                    break
        return self.pop_symbol(tmp[1:])

    def rise_symbol(self, byte_line):
        symbol = b''
        tmp = byte_line
        count = 0
        if not byte_line:
            return None, b''
        while byte_line:
            symbol = byte_line[-1:] + symbol
            byte_line = byte_line[:-1]
            try:
                symbol.decode(ENCODING)
                return symbol, byte_line
            except:
                count += 1
                if count == 6:
                    break
        return self.rise_symbol(tmp[:-1])

    def attach_logger(self, logger):
        self.screen.clear()
        self.loading = True
        # set loading status
        # format_width = self.width
        d = b''.join([x.encode() for x in logger.history])
        self.data = [b'']
        for i in range(self.height+1):
            d = self.load_data_line(d)
        h = self.height - self.margin
        if len(self.data) > h:
            l = len(self.data) - h
        else:
            l = 0
        self.cursor_y = 0
        self.cursor_x = 0
        # t = 0
        while h:
            self.print_data(self.data[l], False)
            l += 1
            h -= 1
            if l == len(self.data):
                break
            self.cursor_y = self.height - self.margin - h
        self.attached_loggers_names.append(logger.name)
        self.update_header()
        if self.data[len(self.data)-1]:
            self.data.append(b'')
        self.screen.noutrefresh()
        self.doupdate()
        logger.pipe_writer = self.terminal.log_display_writer
        asyncio.async(self.load_data(d))
        # load and fromat first n records from buffer  and display it
        # start async formating rest buffer
        # once buffer formated set status loaded
        # fix scrolling fucntion to not able scroll while loading

    def print_data(self, data, refresh=True):
        # print data until line ended or line break or data ended
        while data:
            # if cursor y position out of screen scroll screen
            if self.cursor_y == (self.height-self.margin):
                self.screen.scrollok(True)
                self.screen.scroll()
                self.screen.scrollok(False)
                self.cursor_y -= 1
            try:    
                self.screen.move(self.cursor_y, self.cursor_x)
            except: pass
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
                except:
                    pass
                self.cursor_x += 1
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

    @asyncio.coroutine
    def set_inactive(self):
        yield from self.scroll_end()
        self.active = False
        self.update_header()
        self.doupdate()

    @asyncio.coroutine
    def set_active(self):
        curses.curs_set(0)
        self.active = True
        self.update_header()
        self.doupdate()
