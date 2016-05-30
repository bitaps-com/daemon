import locale

PATH = ''

 


CRITICAL = 60
FATAL = 50
ERROR = 40
WARNING = 30
WARN = WARNING
INFO = 20
DEBUG = 10
DEBUGI = 8
DEBUGII = 6
DEBUGIII = 4
NOTSET = 0

LEVEL_NAMES = {
    60: 'CRITICAL',    # black
    50: 'FATAL',       # red
    40: 'ERROR',       # green
    30: 'WARNING',     # yellow
    20: 'INFO',        # blue
    10: 'DEBUG',       # magenta
    8: 'DEBUG_I',      # cyan
    6: 'DEBUG_II',     # white
    4: 'DEBUG_III',    # default
    0: 'NOTSET',       # default
}



ATERM_CONSOLE_COMMANDS = None
LOG_DISPLAY_WRITER = False
ATTACHED_LOGGERS = False

HEADER = 1
PANEL = 2
PANEL_BACKGROUND = 233
ACTIVE_HEADER = 3
CONSOLE_PANEL_BACKGROUND = 201
CONSOLE_PANEL = 20

RED = 4
GREEN = 5
YELLOW = 6
BLUE = 7
MAGENTA = 8
CYAN = 9
WHITE = 10
GRAY = 11
ALERT = 12
PINK = 13

L_MSG_DEBUG = GREEN
L_MSG_INFO = WHITE
L_MSG_WARNING = YELLOW
L_MSG_ERROR = PINK
L_MSG_FATAL = RED
L_MSG_CRITICAL = RED
L_CREATED = GRAY
L_EXC_INFO = GRAY
L_FILENAME = CYAN
L_FUNCNAME = MAGENTA
L_LEVELNAME = GRAY
L_LEVELNO = GRAY
L_LINENO = BLUE
L_MODULE = CYAN
L_MSECS = GRAY
L_NAME = BLUE
L_PATHNAME = CYAN
L_PROCESS = GRAY
L_PROCESSNAME = GRAY
L_THREAD = GRAY
L_THREADNAME = GRAY


LEVEL_COLORS = {
    0:  L_MSG_FATAL,
    4:  L_MSG_DEBUG,
    6:  L_MSG_DEBUG,
    8:  L_MSG_DEBUG,
    10: L_MSG_DEBUG,
    20: L_MSG_INFO,
    30: L_MSG_WARNING,
    40: L_MSG_ERROR,
    50: L_MSG_CRITICAL,
    60: L_MSG_CRITICAL,
}


ENCODING = locale.getpreferredencoding() or sys.getdefaultencoding()
MASTER_KEYS = ['<BTAB>']
LAST_ERR = b''

FOREGROUND_COLOR_CODES = {
    b'\033[30m': 0,    # black
    b'\033[31m': 0,    # red
    b'\033[32m': 0,    # green
    b'\033[33m': 0,    # yellow
    b'\033[34m': 0,    # blue
    b'\033[35m': 0,    # magenta
    b'\033[36m': 0,    # cyan
    b'\033[37m': 0,    # white
    b'\033[39m': 0,    # default
}

TCL = {
    'gray':   '\033[11m',    # black
    'red':     '\033[12m',    # red
    'pink':     '\033[13m',    # red
    'green':   '\033[5m',    # green
    'yellow':  '\033[6m',    # yellow
    'blue':    '\033[7m',    # blue
    'magenta': '\033[8m',    # magenta
    'cyan':    '\033[9m',    # cyan
    'white':   '\033[10m',    # white
    'default': '\033[2m',    # default
}

BACKGROUND_COLOR_CODES = {
    b'\033[40m': 0,    # black
    b'\033[41m': 0,    # red
    b'\033[42m': 0,    # green
    b'\033[43m': 0,    # yellow
    b'\033[44m': 0,    # blue
    b'\033[45m': 0,    # magenta
    b'\033[46m': 0,    # cyan
    b'\033[47m': 0,    # white
    b'\033[49m': 0,    # default
}

KEY_NAMES = {
    b'\r':          '<ENTER>',
    b'\t':          '<TAB>',
    b'\x1B[Z':      '<SHIFT-TAB>',
    b'\x1B[A':      '<UP>',
    b'\x1B[B':      '<DOWN>',
    b'\x1B[C':      '<RIGHT>',
    b'\x1B[D':      '<LEFT>',
    b'\x1BOA':      '<UP>',
    b'\x1BOB':      '<DOWN>',
    b'\x1BOC':      '<RIGHT>',
    b'\x1BOD':      '<LEFT>',
    b'\x1B[1;5A':   '<CTRL+UP>',
    b'\x1B[1;5B':   '<CTRL+DOWN>',
    b'\x1B[1;5C':   '<CTRL+RIGHT>',
    b'\x1B[1;5D':   '<CTRL+LEFT>',
    b'\x1B[5A':     '<CTRL+UP>',
    b'\x1B[5B':     '<CTRL+DOWN>',
    b'\x1B[5C':     '<CTRL+RIGHT>',
    b'\x1B[5D':     '<CTRL+LEFT>',
    b'\x1B[1;2A':   '<SHIFT+UP>',
    b'\x1b[5~':     '<SHIFT+UP>',
    b'\x1b[6~':     '<SHIFT+DOWN>',
    b'\x1B[1;2B':   '<SHIFT+DOWN>',
    b'\x1B[1;2C':   '<SHIFT+RIGHT>',
    b'\x1B[1;2D':   '<SHIFT+LEFT>',
    b'\x1B[1;9A':   '<ESC+UP>',
    b'\x1B[1;9B':   '<ESC+DOWN>',
    b'\x1B[1;9C':   '<ESC+RIGHT>',
    b'\x1B[1;9D':   '<ESC+LEFT>',
    b'\x1B[1;10A':  '<ESC+SHIFT+UP>',
    b'\x1B[1;10B':  '<ESC+SHIFT+DOWN>',
    b'\x1B[1;10C':  '<ESC+SHIFT+RIGHT>',
    b'\x1B[1;10D':  '<ESC+SHIFT+LEFT>',
    b'\x1BOP':      '<F1>',
    b'\x1BOQ':      '<F2>',
    b'\x1BOR':      '<F3>',
    b'\x1BOS':      '<F4>',
    b'\x1B[15~':    '<F5>',
    b'\x1B[17~':    '<F6>',
    b'\x1B[18~':    '<F7>',
    b'\x1B[19~':    '<F8>',
    b'\x1B[20~':    '<F9>',
    b'\x1B[21~':    '<F10>',
    b'\x1B[23~':    '<F11>',
    b'\x1B[24~':    '<F12>',
    b'\x00':        '<CTRL+SPACE>',
    b'\x1C':        '<CTRL+\\>',
    b'\x1D':        '<CTRL+]>',
    b'\x1E':        '<CTRL+6>',
    b'\x1F':        '<CTRL+/>',
    b'\x7F':        '<BACKSPACE>',
    b'\x1B\x7F':    '<ESC+BACKSPACE>',
    b'\xFF':        '<META-BACKSPACE>',
    b'\x1B\x1B[A':  '<ESC+UP>',
    b'\x1B\x1B[B':  '<ESC+DOWN>',
    b'\x1B\x1B[C':  '<ESC+RIGHT>',
    b'\x1B\x1B[D':  '<ESC+LEFT>',
    b'\x1B':        '<ESC>',
    b'\x1B[1~':     '<HOME>',
    b'\x1BOH':      '<HOME>',
    b'\x1B[2~':     '<PADENTER>',
    b'\x1B[3~':     '<PADDELETE>',
    b'\x1B[4~':     '<END>',
    b'\x1BOF':      '<END>',
    b'\x1B[5~':     '<PAGEUP>',
    b'\x1B[6~':     '<PAGEDOWN>',
    b'\x1B\x1B[5~': '<ESC+PAGEUP>',
    b'\x1B\x1B[6~': '<ESC+PAGEDOWN>',
    b'\x1B[H':      '<HOME>',
    b'\x1B[F':      '<END>',
    b'\x1BOP':      '<F1>',
    b'\x1BOQ':      '<F2>',
    b'\x1BOR':      '<F3>',
    b'\x1BOS':      '<F4>',
    b'\x1B[15~':    '<F5>',
    b'\x1B[17~':    '<F6>',
    b'\x1B[18~':    '<F7>',
    b'\x1B[19~':    '<F8>',
    b'\x1B[20~':    '<F9>',
    b'\x1B[21~':    '<F10>',
    b'\x1B[23~':    '<F11>',
    b'\x1B[24~':    '<F12>',
    b'\x1B[A':      '<UP>',
    b'\x1B[B':      '<DOWN>',
    b'\x1B[C':      '<RIGHT>',
    b'\x1B[D':      '<LEFT>',
    b'\x08':        '<BACKSPACE>',
    b'\x1B[3~':     '<DEL>',
    b'\x1B[Z':      '<BTAB>',
}

MAX_KEYPRESS_SIZE = max(len(seq) for seq in list(KEY_NAMES.keys()))
READ_SIZE = 512
