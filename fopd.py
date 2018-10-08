# This module is the main program.
#
# Run this program from the command line as per:
#   cd /home/pi/openag-mvp
#   python3 mvp.py
#
#   Note: pythone3 mvp.py --help  -> Will display available command line arguments.
#
# or run the program at startup as a systemd service using the following service file contents:
# edited to fit your particular situation.
"""
[Unit]
Description=fopd
Wants=network-online.target
After=network-online.target

[Service]
WorkingDirectory=/home/pi/fopd
User=pi
ExecStart=/home/pi/fopd/venv/bin/python  /home/pi/fopd/fopd.py --silent
Restart=on-failure

[Install]
WantedBy=multi-user.target
"""
#
# Notes on systemd
#
# 1) If your program uses a virtual environment then use the python located in the virtual environment bin folder.
#    (e.g. /home/pi/fopd/venv/bin/python)
# 2) In order to tell your Linux OS to start the systemd service on boot, run the following command:
#    sudo systemctl enable fopd
#    The above command assumes that your systemd service file is named fopd.service.
# 
#
# The mvp provides a REPL loop for interactive operation. This loop can be turned off
# by invoking the mvp in silent mode. (i.e. --silentysm as a python argument to the invocation of fopd.py.
#
# It is assumed that mvp.py is located in a directory that contains code and data organized
# identical to the way it is stored in github (https://github.com/ferguman/fopd)
# 

# Ok let's get started!

# Make sure we are running a compatible version of python.
from check_python_version import check_python_version
check_python_version()

from python.logger import get_top_level_logger
from python.verify_config_files import verify_config_file
logger = get_top_level_logger()

logger.info('############## starting farm operation platform device ################')

# Check that the configuration file is present and then load it.
verify_config_file()

# After the above check we know it's safe to load the rest of the modules.
from importlib import import_module
import threading

# Load mvp libraries
from config.config import system
from web.flask_app import run_flask 
from python.args import get_args
from python.repl import start

# Process the command line args
args = get_args()

logger.info('fopd device id: {}'.format(system['device_id']))

# TODO: I think we can take cmds out. 
# Some threads such as repl and web chart generator expose functions on 'sys', so
# add the 'sys' key for them to tack stuff onto. 
s = {'name': system['name']}
app_state = {'system': s, 'cmds':{}, 'stop': False, 'silent_mode':args.silent, 'sys':{'cmd':None}}

# create a Barrier that all the threads can syncronize on. This is to
# allow threads such as mqtt or data loggers to get initialized before
# other threads try to call them.
#
b = threading.Barrier(len(system['resources']), timeout=20) 

# Each resource is implemented as a thread. Setup all the threads.
tl = []
for r in system['resources']:

    m = import_module(r['imp'])

    tl.append(threading.Thread(target=m.start, name=r['args']['name'], args=(app_state, r['args'], b)))

# start the built in REPL interpretter.
#- if not args.silent:
#- tl.append(threading.Thread(target=repl, name='repl', args=(app_state, args.silent)))
tl.append(threading.Thread(target=start, name='repl', args=(app_state, args.silent)))

# Start all threads
for t in tl:
    t.start()
    
# TODO: Consider running the CherryPy web server (instead of the Werkzeug server) as
#       the front end to Flask. If CherryPy can run as a seperate thread then this
#       main thread could stop the server. See flask.pocoo.org/snippets/24/ for further
#       details.
# Start the Flask application
#
run_flask(app_state)

app_state['stop'] = True

# Wait for threads to complete.
#
for t in tl:
    t.join()
