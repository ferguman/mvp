# This module is the main program.
#
# Run this program from the command line as per:
#   cd /home/pi/openag-mvp
#   python3 mvp.py
#
#   Note: pythone3 mvp.py --help  -> Will display available command line arguments.
#
# or run the program at startup as a systemd service using the following service file contents:
#    [Unit]
#    Description=mvp
#    Wants=network-online.target
#    After=network-online.target
#
#    [Service]
#    WorkingDirectory=/home/pi/openag-mvp
#    User=pi
#    ExecStart=/usr/bin/python3 /home/pi/openag-mvp/mvp.py --silent
#    Restart=on-failure
#
#    [Install]
#    WantedBy=multi-user.target
#
#
# The mvp provides a REPL loop for interactive operation. This loop can be turned off
# by invoking the mvp in silent mode.
#
# It is assumed that mvp.py is located in a directory that contains code and data organized
# identical to the way it is stored in github (https://github.com/ferguman/fopd)
# 

# Ok let's get started!

# Make sure we are running a compatible version of python.
from check_python_version import check_python_version
check_python_version()

from python.mvp_logger import get_logger
from python.verify_config_files import verify_config_file
logger = get_logger()

logger.info('############## starting mvp')

# Check that the configuration file is present and then load it.
verify_config_file()

# After the above check we know it's safe to load the rest of the modules.
from importlib import import_module
import threading

# Load mvp libraries
from config.config import system
#- from python.adjustThermostat import start_fan_controller
from python.args import get_args
#- from python.camera_controller import start_camera_controller
#- from python.light_controller import start_light_controller
#- from python.logSensors import start_sensor_data_logger
#- from python.mqtt_client import start_mvp_mqtt_client
from python.repl import repl
#- from python.web_chart_controller import start_web_chart_controller

# Process the command line args
args = get_args()

logger.info('############## fopd device id: {}'.format(system['device_id']))

app_state = {'stop': False, 'silent_mode':args.silent}

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

# Start all threads
for t in tl:
    t.start()

if not args.silent:
    repl(app_state)

# Wait for threads to complete.
#
for t in tl:
    t.join()
