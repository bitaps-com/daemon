import asyncio,os
from .constants import *
import fcntl
 

def set_nonblocking(file_handle):
    """Make a file_handle non-blocking."""
    OFLAGS = fcntl.fcntl(file_handle, fcntl.F_GETFL)
    nflags = OFLAGS | os.O_NONBLOCK
    fcntl.fcntl(file_handle, fcntl.F_SETFL, nflags)



class Server:
    def __init__(self, o, e, l, i, stdout_port, stderr_port, logger_port, stdin_port):
        self.socket_stdout = []
        self.socket_logger = []
        self.socket_stderr = []
        self.o             = o
        self.l             = l
        self.e             = e
        self.i             = i
        set_nonblocking(self.o)
        set_nonblocking(self.l)
        set_nonblocking(self.e)
        self.loop          = asyncio.get_event_loop()
        stdout_port        = asyncio.start_server(self.handle_stdout, '127.0.0.1', stdout_port)
        logger_port        = asyncio.start_server(self.handle_logger, '127.0.0.1', logger_port)
        stderr_port        = asyncio.start_server(self.handle_stderr, '127.0.0.1', stderr_port)
        stdin_port         = asyncio.start_server(self.handle_stdin, '127.0.0.1', stdin_port)
        self.loop.add_reader(self.o, self.stdout_data_received)
        self.loop.add_reader(self.l, self.logger_data_received)
        self.loop.add_reader(self.e, self.stderr_data_received)
        asyncio.async(stdout_port)
        asyncio.async(logger_port)
        asyncio.async(stderr_port)
        asyncio.async(stdin_port)
        self.loop.run_forever()
        self.loop.close()

    @asyncio.coroutine
    def handle_stdin (self, reader, writer):
        while True:
            r = yield from reader.readline()
            if not r:
                return
            try:
                self.i.write(r)
                self.i.flush()
            except Exception as err:
                #print('>%s' % err)
                return

    @asyncio.coroutine
    def handle_stdout (self, reader, writer):
        # print('connectedd')
        self.socket_stdout.append(writer._transport._sock)  

    def stdout_data_received(self):
        #print('>>>')
        try:
            data = os.read(self.o.fileno(), 4096)
        except:
            return
        if not data:
            self.loop.stop()
            return 
        f = open('console.log','a+')
        f.write(data.decode())
        f.close()
        for socket in self.socket_stdout:
            try:
                socket.send(data)
            except:
                self.socket_stdout.remove(socket)

    @asyncio.coroutine
    def handle_stderr (self, reader, writer):
        self.socket_stderr.append(writer._transport._sock)  

    def stderr_data_received(self):
        try:
            data = os.read(self.e.fileno(), 4096)
        except:
            return
        if not data:
            self.loop.stop()
            return 
        f = open('error.log','a+')
        f.write(data.decode())
        f.close()
        for socket in self.socket_stderr:
            try:
                socket.send(data[:4096])
            except:
                self.socket_stderr.remove(socket)

    @asyncio.coroutine
    def handle_logger (self, reader, writer):
        self.socket_logger.append(writer._transport._sock)                  

    def logger_data_received(self):
        try:
            data = os.read(self.l.fileno(), 4096)
        except:
            return
        if not data:
            self.loop.stop()
            return 
        for socket in self.socket_logger:
            try:
                socket.send(data[:4096])
            except:
                self.socket_logger.remove(socket)

