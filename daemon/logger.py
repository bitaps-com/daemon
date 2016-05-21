import re
import sys
import time
from .constants import *

try:
    getattr(sys.modules['__main__'], 'LOGGER_DICT')
except:
    setattr(sys.modules['__main__'],'LOGGER_DICT', dict())

HOME_DIR  =  ''

def getLogger(name, file = True,path = None, visible = True,level = NOTSET):
    try:
        getattr(sys.modules['__main__'], 'LOGGER_DICT')
    except:
        setattr(sys.modules['__main__'],'LOGGER_DICT', dict())
    if not path:
        try:
            HOME_DIR = getattr(sys.modules['__main__'], 'HOME_DIR')
            path = HOME_DIR +'/'+ name + '.log'
        except:
            pass        
    logger_dict = getattr(sys.modules['__main__'], 'LOGGER_DICT')
    if name not in logger_dict:
        logger_dict[name] = Logger(name,path = path, level = level)
    return logger_dict[name]

def removeLogger(name):
   try:
       logger_dict = getattr(sys.modules['__main__'], 'LOGGER_DICT')
       del  logger_dict[name]
   except Exception as err:
       print('removelogger %s' % err) 


class Logger:
    BUFFER_LIMIT    = 1024 * 1024 * 12
    raw_buffer      = bytearray()
    log_file_name   = None
    socket          = sys.stdout
    level           = NOTSET


    def __init__(self, name='root', path = None,visible = True, level = NOTSET):
        # setattr(sys.modules['__main__'],'LOGGER_PIPE', os.fdopen(_logger_writer,'wb'))
        self.level = level
        self.name = name
        self.socket_relay = visible
        if path:
            self.log_file_name = path
            



    def log(self, message, level = NOTSET):
        if self.level > level:
            return
        message += '\n'
        if self.log_file_name is not None:
            # if message[-1:]!='\n':
            # message += '\n'
            m =  re.sub("\033\[\d+m", "", message)
            self.write_to_file(('%s [%s]: %s' % (int(time.time()),LEVEL_NAMES[level],m)).encode()) 
        # if self.socket_relay:
        if True:
            if sys.modules['__main__'].LOGGER_PIPE is not None:
                restore_panel_color = '\033[%sm' % PANEL
                f = '\033[%sm%s' % (L_NAME, self.name)
                f += '\033[%sm[%s]: ' % (L_LEVELNAME, LEVEL_NAMES[level])
                f += '\033[%sm%s%s' % (LEVEL_COLORS[level], message, restore_panel_color)
                self.raw_buffer += f.encode() 
                self.write(self.raw_buffer)
                # if len(self.raw_buffer) > self.BUFFER_LIMIT:
                #     self.raw_buffer[:len(self.raw_buffer)-self.BUFFER_LIMIT] = []
            else:
                print('%s [%s]: %s' % (int(time.time()),LEVEL_NAMES[level],message)) 

    def setLevel(self,level):
        self.level = level
        print('Logger %s set to %s' % (self.name, LEVEL_NAMES[level]) )


    def warning(self,message):
        self.log(message,WARNING)

    def error(self,message):
        self.log(message,ERROR)

    def info(self,message):
        self.log(message,INFO)

    def critical(self,message):
        self.log(message,CRITICAL)

    def debug(self,message):
        self.log(message,DEBUG)

    def debugI(self,message):
        self.log(message,DEBUGI)

    def debugII(self,message):
        self.log(message,DEBUGII)

    def debugIII(self,message):
        self.log(message,DEBUGIII)


         
    def write_to_file(self, data):
        if self.log_file_name is not None:
            try:
                f = open(self.log_file_name,'a+')
                f.write(data.decode())
                f.close()
            except Exception as err:
                sys.stderr.write('%s write error:%s\n' % (self.log_file_name,err))
                sys.stderr.flush()

    def write(self, data):
        while data:
            try:
                sys.modules['__main__'].LOGGER_PIPE.write(data[-4096:])
                sys.modules['__main__'].LOGGER_PIPE.flush()
            except Exception as err:
                sys.stderr.write('logger pipe write  error:%s\n'%err)
                sys.stderr.flush()
                return
            data[-4096:] = []
