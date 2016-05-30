import asyncio, sys, locale, curses, fcntl, os, socket, re, signal


from .constants import *
from .console import *




locale.setlocale(locale.LC_ALL, '')
code = locale.getpreferredencoding()

def set_nonblocking(file_handle):
    """Make a file_handle non-blocking."""
    OFLAGS = fcntl.fcntl(file_handle, fcntl.F_GETFL)
    nflags = OFLAGS | os.O_NONBLOCK
    fcntl.fcntl(file_handle, fcntl.F_SETFL, nflags)




class Terminal:

    def __init__(self, split_height, stdout_port, stderr_port, logger_port, stdin_port):
        self.fid_lock = None
        self.split_height = split_height
        self.name = 'test'
        self.loop = asyncio.get_event_loop()
        self.widget = []
        self.stdout_port = stdout_port
        self.stderr_port = stderr_port
        self.logger_port = logger_port
        self.stdin_port = stdin_port
        self.active_widget = None
        self.curses_screen = False
        self.y_size_base = 0
        self.x_size_base = 0
        self.stdin_buffer = b''
        self.logger = None
        self.cursor_x = 10
        self.cursor_y = 10
        self.log_display_writer = None
        self.hook_stdin_stream()
        self.loop.add_signal_handler(28, self.resize)
        self.width, self.height = os.get_terminal_size()
        

    def __del__(self):
        if self.curses_screen:
            self.restore_screen()
        #if self.fid_lock is not None:
        #    self.fid_lock.close()



    def excepthook_from_curses_mode(self, type, value, traceback):
        curses.nocbreak()
        curses.echo()
        curses.endwin()
        #sys.stdout.buffer.write(b'\033[31m--- Last stderr Record ---\033[0m\n')
        #sys.stdout.buffer.write(LAST_ERR + b'\033[1;0m')
        #print('\033[31m--- Except Hook ---\033[0m')
        #sys.__excepthook__(type, value, traceback)

    def hook_stdin_stream(self):
        self.stdin_data_receved = asyncio.Event()
        fd = sys.stdin.fileno()
        fl = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
        self.loop.add_reader(sys.stdin, self.stdin_data_receved.set)

    @asyncio.coroutine
    def stdin_reader(self):
        while True:
            key = yield from self.getch()
            if key == '<BTAB>':
                yield from self.change_active_widget()
                continue
            yield from asyncio.async(self.process_key(key))

    @asyncio.coroutine
    def getch(self):
        key_name = None
        while True:
            try:

                key_name = self.decode_key_from_buffer()
                if key_name is not None:
                    return key_name
                key = os.read(sys.stdin.fileno(), READ_SIZE)
                if len(key) == 0:
                    raise
                self.stdin_buffer = self.stdin_buffer + key
            except:
                yield from self.stdin_data_receved.wait()
                self.stdin_data_receved.clear()

    @asyncio.coroutine
    def process_key(self, key):
        if self.active_widget is None:
            return info("No active widget")
        # try:
        yield from self.widget[self.active_widget].process_key(key)
        # except Exception as err:
            # print(err)

    @asyncio.coroutine
    def change_active_widget(self):
        yield from self.widget[self.active_widget].set_inactive()
        self.active_widget += 1
        if self.active_widget > (len(self.widget)-1):
            self.active_widget = 0
        yield from self.widget[self.active_widget].set_active()



    def decode_key_from_buffer(self):
        if len(self.stdin_buffer) == 0:
            return None
        ln = 6
        buffer_len = len(self.stdin_buffer)
        if ln > buffer_len:
            ln = buffer_len
        while ln:    # try to decode key from key name list
            key = self.stdin_buffer[0:ln]
            if key in KEY_NAMES:
                self.stdin_buffer = self.stdin_buffer[ln:]
                return KEY_NAMES[key]
            ln -= 1
        ln = 1
        while True:    # try to decode key with current encoding
            key = self.stdin_buffer[0:ln]
            try:
                key = key.decode(ENCODING)
                self.stdin_buffer = self.stdin_buffer[ln:]
                return key
            except:
                pass
            ln += 1
            if ln > MAX_KEYPRESS_SIZE or ln > buffer_len:
                break
        sys.stderr.write('Cannot decode bytes on stdin chanel')
        self.stdin_buffer = self.stdin_buffer[1:]
        return None

    def resize(self):
        # TODO 
        # resize widget calculations 
        # at this moment only static size
        ts = os.get_terminal_size()
        self.screen_height, self.screen_width = ts.lines , ts.columns
        curses.resizeterm(self.screen_height, self.screen_width)
        self.width, self.height = os.get_terminal_size()
        self.screen.clear()
        self.screen.bkgd(curses.color_pair(PANEL))
        curses.curs_set(0)
        self.screen.refresh()
        # recalculate all widget size widget by widget


        self.widget[0].rh = math.floor(self.height * (1 - 0.5))
        # self.widget[0].rh = self.height 
        self.widget[1].rh = self.height - self.widget[0].rh 
        self.widget[1].widget_heights =  self.widget[0].rh
        for w in self.widget:
            # try:
            w.resize()
            # except:
            #     pass
        
                

    def init_screen(self):
        TERM = os.environ['TERM']
        TERM256COLOR = True
        try:
            os.environ['TERM'] = 'xterm-256color'
            self.screen = curses.initscr()
        except Exception as e:
            print(e)
            print('256  color mode terminal not found')
            TERM256COLOR = False
            os.environ['TERM'] = TERM
            self.screen = curses.initscr()
        curses.noecho()
        curses.cbreak()
        curses.curs_set(0)
        self.screen.keypad(1)
        if curses.has_colors():
            curses.start_color()
            if TERM256COLOR:
                curses.init_pair(1, 247, 237)
                curses.init_pair(PANEL, 255, PANEL_BACKGROUND)
                curses.init_pair(RED, 1, PANEL_BACKGROUND)
                curses.init_pair(GREEN, 2, PANEL_BACKGROUND)
                curses.init_pair(YELLOW, 3, PANEL_BACKGROUND)
                curses.init_pair(BLUE, 4, PANEL_BACKGROUND)
                curses.init_pair(MAGENTA, 5, PANEL_BACKGROUND)
                curses.init_pair(CYAN, 6, PANEL_BACKGROUND)
                curses.init_pair(WHITE, 7, PANEL_BACKGROUND)
                curses.init_pair(GRAY, 241, PANEL_BACKGROUND)
                curses.init_pair(ALERT, 1, PANEL_BACKGROUND)
                curses.init_pair(ACTIVE_HEADER, 11, 238)
                curses.init_pair(PINK,  204, PANEL_BACKGROUND)
                curses.init_pair(CONSOLE_PANEL,  204, CONSOLE_PANEL_BACKGROUND)

            else:
                curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
                curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)
                curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLACK)
                curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_BLACK)
        else:
            curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
            curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)
            curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLACK)
            curses.init_pair(5, curses.COLOR_WHITE, curses.COLOR_BLACK)
        self.screen_height, self.screen_width = self.screen.getmaxyx()
        self.screen.bkgd(curses.color_pair(0))

    def restore_screen(self):
        curses.nocbreak()
        curses.echo()
        curses.endwin()


    def add(self, widget_class):

        self.widget.append(widget_class(self, self.split_height, 
                           self.stdout_port, self.stderr_port, 
                           self.logger_port, self.stdin_port))
        return self

    def simple_mode(self):
        fout = os.fdopen(sys.stdout.fileno(), 'wb')
        ferr = os.fdopen(sys.stdout.fileno(), 'wb')
        fin = os.fdopen(sys.stdin.fileno(), 'rb')
        # try:
        stdout = socket.socket()
        stdout.connect(('127.0.0.1',self.stdout_port))
        stderr = socket.socket()
        stderr.connect(('127.0.0.1',self.stderr_port))
        logger = socket.socket()
        logger.connect(('127.0.0.1',self.logger_port))
        stdin = socket.socket()
        stdin.connect(('127.0.0.1',self.stdin_port))
        set_nonblocking(stdout)
        set_nonblocking(stderr)
        set_nonblocking(stdin)

        # except Exception as err:
        #     print(err)
        #     self.loop.stop()
        #     print("Can't connect to daemon [daemon already terminated or virtual console failed]")


        def stdout_data_received():
            try:
                data = os.read(stdout.fileno(), 4096)
            except:
                return
            if not data:
                return                
            fout.write(data)
            fout.flush()

        def stderr_data_received():
            try:
                data = os.read(stderr.fileno(), 4096)
            except:
                return
            if not data:
                eof()
                return                
            ferr.write(data)
            ferr.flush()

        def logger_data_received():
            try:
                data = os.read(logger.fileno(), 4096)
            except:
                return 
            if not data:
                eof()
                return                
            data_list = re.sub(b"\033\[\d+m", b"", data).split(b'\n')
            for data in data_list:
                c = b'\x1b[31;1m'
                if data.find(b'[INFO]')+1 : c = b'\x1b[39;1m'
                if data.find(b'[ERROR]')+1 : c = b'\x1b[31;1m'
                if data.find(b'[CRITICAL]')+1 : c = b'\x1b[31;1m'
                if data.find(b'[DEBUG]')+1 : c = b'\x1b[32;1m'
                if data.find(b'[DEBUG_I]')+1 : c = b'\x1b[36;1m'
                if data.find(b'[DEBUG_II]')+1 : c = b'\x1b[35;1m'
                if data.find(b'[DEBUG_III]')+1 : c = b'\x1b[34;1m'
                if data.find(b'[WARNING]')+1 : c = b'\x1b[33;1m'
                if data:
                    fout.write(c+data+ b'\x1b[0m\n')
            fout.flush()

        def stdin_data_received():
            try:
                data = os.read(fin.fileno(), 4096)
            except:
                return
            if not data:
                eof()
                return
            if data == b'kill\n':
                HOME_DIR = getattr(sys.modules['__main__'], 'HOME_DIR')
                f = open(HOME_DIR +'/pid', 'r')
                i = f.read()
                f.close()
                try:
                    os.kill(int(i),signal.SIGTERM )
                    print('Kill command sent to daemon')
                except Exception as err:
                    print('Kill command error: %s' % err)
                return

            stdin.send(data)
        def signal_handler(signal, frame):
            print("\nTerminal disconnected from daemon")
            self.loop.stop()

        def eof():
            self.loop.stop()


        @asyncio.coroutine
        def shutdown():
            self.loop.stop()
        signal.signal(signal.SIGINT, signal_handler)
        try:
            self.loop.add_reader(stdout, stdout_data_received)
            self.loop.add_reader(stderr, stderr_data_received)
            self.loop.add_reader(logger, logger_data_received)
            # newin = os.fdopen(sys.stdin.fileno(), 'r', 1)

            fcntl.fcntl(sys.stdin.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)
            self.loop.add_reader(sys.stdin, stdin_data_received)
        except:
            asyncio.async(shutdown())



    def start(self):
        if  self.widget:
            if not self.curses_screen:
                self._excepthook = sys.excepthook
                sys.excepthook = self.excepthook_from_curses_mode
                self.curses_screen = True
                self.init_screen()
                self.hook_stdin_stream()
            self.active_widget = len(self.widget)-1
            self.widget[self.active_widget].active = True
            asyncio.async(self.stdin_reader())
            for widget in self.widget:
                widget.start()
        else:
            self.simple_mode()
        self.loop.run_forever()
        self.loop.close()
        return self
   