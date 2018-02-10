import os, sys
import bjoern
import daemon
# import logging
from daemon.pidfile import PIDLockFile
from kaqpay import app

if __name__ == '__main__':
    current_dir = os.abspath(os.path.dirname(sys.argv[0]))

    if app.config.has_key('PID_FILE'):
        pidfile = PIDLockFile(app.config.get('PID_FILE'))
        if pidfile.is_locked():
            print("Running Already (pid: %d)".format(pidfile.read_pid()))

    # can use logging but why make things complicated?
    if app.config.has_key('STDOUT_LOG')
        stdout = open(app.config.get('STDOUT_LOG'))
    if app.config.has_key('STDERR_LOG'):
        stderr = open(app.config.get('STDERR_LOG'))

    ctx = daemon.DaemonContext(
            working_directory=current_dir,
            umask=0o002,
            pidfile=pidfile,
            stdout=stdout,
            stderr=stderr)
        
    with ctx:
        bjoern.run(app, 'localhost', 9090)
