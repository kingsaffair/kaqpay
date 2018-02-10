import os, sys
import bjoern
import daemon
# import logging
from daemon.pidfile import PIDLockFile
from kaqpay import app

if __name__ == '__main__':
    current_dir = os.getcwd()
    pidfile = PIDLockFile(app.config.get('PID_FILE'))
    if pidfile.is_locked():
        print("Running Already (pid: %d)".format(pidfile.read_pid()))

    # can use logging but why make things complicated?
    stdout = open(app.config.get('STDOUT_LOG'), 'w+')
    stderr = open(app.config.get('STDERR_LOG'), 'w+')

    ctx = daemon.DaemonContext(
            working_directory=current_dir,
            umask=0o002,
            pidfile=pidfile,
            stdout=stdout,
            stderr=stderr)
        
    with ctx:
        bjoern.run(app, 'localhost', 9091)
