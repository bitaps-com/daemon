# Python daemonizer package

This is a Python module that will daemonize your Python script so it can continue running in the background. It works on Unix, Linux and OS X, creates a PID file and has standard commands (start, stop, virtual console), integrated logger.



# Usage

```import daemon
daemon.start()

... 
rest code will be executed as daemon
```
# Command line arguments

###--terminal  
    If daemon not yet started, start daemon and forward all output to console.
    CTRL+C stop console, but daemon continue working.
    If daemon already started connect to dameon virtual console and forward output to console. All inputs from console forward to daemon process stdin.

###--xterminal
    Same as --terminal but Start advanced vitual console.

###--stop
    Terminate daemon.


# Integrated logger

```
...
logger = daemon.getLogger('test')

log.info('info message')
log.error('error message')
log.debug('debug message')

...
logger.setLevel(daemon.WARNING)
...
```


