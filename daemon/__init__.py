import sys
import os
import time
import fcntl
import atexit
import signal
from .terminal import *    
from .server   import *    
from .console  import *
from .logger   import *
from .logwin   import *


try:
    getattr(sys.modules['__main__'], 'LOGGER_PIPE')
except:
    setattr(sys.modules['__main__'],'LOGGER_PIPE', None)
    
# parsing arguments
# todo deamon stop argument wait unitl process stopeed
def start():    


    try:
        HOME_DIR = getattr(sys.modules['__main__'], 'HOME_DIR')
    except:
        HOME_DIR =  os.getenv("HOME")+'/.'+sys.argv[0]
        if HOME_DIR[-3:] == '.py':
            HOME_DIR = HOME_DIR[:-3]
        if not os.path.exists(HOME_DIR):
            os.makedirs(HOME_DIR,755)
        setattr(sys.modules['__main__'],'HOME_DIR', HOME_DIR)




    TERMINAL = 0
    if '--terminal' in sys.argv:
        TERMINAL = 1

    if '--xterminal' in sys.argv:
        TERMINAL = 2

    if '--stop' in sys.argv:
        try:
            f = open(HOME_DIR +'/pid', 'r')
            i = f.read()
            f.close()
            os.kill(int(i),signal.SIGTERM)
            print('Deamon stopped')
        except Exception as err :
            print(err)
        sys.exit(0)


    # try to start deamon 

    try:
        pid = os.fork()
    except OSError as e:
        sys.stderr.write('Fork #1 failed: %d (%s)\n' % (e.errno, e.strerror))
        sys.exit(1)
    if pid > 0:
        # P1 parent wait child end 
        x = os.wait4(pid, 0)
        if (x[1] >> 8)==1:
            sys.stderr.write('[P1] startup filed\n')
            sys.exit(1)
        if TERMINAL == 0:
            sys.exit(0)
        if TERMINAL == 1:
            print('Start simple terminal')
            t = Terminal().start()
        if TERMINAL == 2:
            print('Start extra terminal')
            t = Terminal().add(LogWin).add(Console).start()
        del t
        sys.exit(0)
    else:
        # C1  Child should try to start deamon
        os.setsid()
        os.chdir('.')
        os.umask(0)
        try:
            pid = os.fork()
        except OSError as e:
            sys.stderr.write('[C1] Fork #2 failed: %d (%s)\n' % (e.errno, e.strerror))
            sys.exit(1)
        if pid > 0:
            #P2  Parent sleep then read pid file
            time.sleep(0.2)
            try:
                f = open(HOME_DIR +'/pid', 'r')
                i = f.read()
                f.close()
            except:
                sys.stderr.write('[P2] Read from %s.pid failed.\n' % (NAME))
                sys.exit(1)
            if i == str(pid):
                    print('Started process id: %s' %pid)
                    sys.exit(2)
            else:
                fid = open(HOME_DIR + '/lock', 'w+')
                try:
                    fcntl.lockf(fid, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except IOError:
                    sys.exit(3) # lock file already locked, so deamon was running early 
            sys.exit(1)
        else:
            #C2 set lock to lock file 
            setattr(sys.modules['__main__'],'DEAMON_LOCK', None)
            sys.modules['__main__'].DEAMON_LOCK = open(HOME_DIR + '/lock', 'w+')
            try:
                fcntl.lockf(sys.modules['__main__'].DEAMON_LOCK, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except IOError:
                sys.stderr.write('[C2] Deamon already started.\n')
                sys.exit(1)

            so = open('/dev/null', 'w')
            se = open('/dev/null', 'w')
            si = open('/dev/null', 'r')
            os.dup2(si.fileno(), sys.stdin.fileno())
            os.dup2(so.fileno(), sys.stdout.fileno())
            os.dup2(se.fileno(), sys.stderr.fileno())

            _stdout_reader, _stdout_writer = os.pipe()
            _stderr_reader, _stderr_writer = os.pipe()
            _stdin_reader,  _stdin_writer  = os.pipe()
            _logger_reader, _logger_writer = os.pipe()

            try:
                pid = os.fork()
            except OSError as e:
                sys.stderr.write('[C2] Fork #1 failed: %d (%s)\n' % (e.errno, e.strerror))
                sys.exit(1)
            if pid > 0:
                #P3 Start main program
                try:
                    f = open(HOME_DIR+ '/pid', 'w+')
                    f.write(str(os.getpid()))
                    f.close()
                except:
                    fid.close()
                    sys.stderr.write('[C2] Write to  %s.pid failed.\n' % (NAME))
                    sys.exit(1)
                os.chdir('.')
                os.umask(0)
                sys.stdout.flush()
                sys.stderr.flush()

                os.close(_stdout_reader)
                os.close(_stderr_reader)
                os.close(_logger_reader)
                os.close(_stdin_writer)

                so = os.fdopen(_stdout_writer,'w')
                se = os.fdopen(_stderr_writer,'w')
                si = os.fdopen(_stdin_reader,'r')
                set_nonblocking(si)
                setattr(sys.modules['__main__'],'LOGGER_PIPE', os.fdopen(_logger_writer,'wb'))
                os.dup2(si.fileno(), sys.stdin.fileno())
                os.dup2(so.fileno(), sys.stdout.fileno())
                os.dup2(se.fileno(), sys.stderr.fileno())

                # main logic
                def kill_child():
                    print('\033[13mDeamon Terminated\033[2m')
                    os.system('kill %s' % pid)
                # def kill_self(a,b):
                #     print('\033[13mDeamon Terminated\033[2m')
                #     os.system('kill %s' % pid)
                #     sys.exit(0)

                atexit.register(kill_child)
                # signal.signal(signal.SIGTERM, kill_self)

            else:
                #C3 Start monitoring server
                try:
                    f = open(HOME_DIR+ '/pid_monitoring', 'w+')
                    f.write(str(os.getpid()))
                    f.close()
                except:
                    fid.close()
                    sys.stderr.write('[C2] Write to  %s.pid failed.\n' % (NAME))
                    sys.exit(1)
                so = open('/dev/null', 'w')
                se = open('/dev/null', 'w')
                si = open('/dev/null', 'r')
                os.dup2(si.fileno(), sys.stdin.fileno())
                os.dup2(so.fileno(), sys.stdout.fileno())
                os.dup2(se.fileno(), sys.stderr.fileno())


                os.close(_stdout_writer)
                os.close(_stderr_writer)
                os.close(_logger_writer)
                os.close(_stdin_reader)

                l = os.fdopen(_logger_reader,'rb')
                o = os.fdopen(_stdout_reader,'rb')
                e = os.fdopen(_stderr_reader,'rb')
                i = os.fdopen(_stdin_writer,'wb')

                Server(o, e, l, i)
                sys.exit(0)
