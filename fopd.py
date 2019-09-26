# This module is the main program.
#
# Run this program from the command line as per:
#   cd /home/pi/openag-mvp
#   python3 mvp.py
#
#   Note: pythone3 mvp.py --help  -> Will display available command line arguments.
#
# or run the program at startup as a systemd service using the following service file contents:
# Notes on systemd
#
# 1) If your program uses a virtual environment then use the python located in the virtual environment bin folder.
#    (e.g. /home/pi/fopd/venv/bin/python)
# 2) In order to tell your Linux OS to start the systemd service on boot, run the following command:
#    sudo systemctl enable fopd
#    The above command assumes that your systemd service file is named fopd.service.
# 
#
# The fopd provides a REPL loop for interactive operation. This loop can be turned off
# by invoking the mvp in silent mode. (i.e. --silent) as a python argument to the invocation of fopd.py.
#
# It is assumed that fopd.py is located in a directory that contains code and data organized
# identical to the way it is stored in github (https://github.com/ferguman/fopd)
# 

# Make sure we are running a compatible version of python.
from check_python_version import check_python_version
if not check_python_version():
    exit('wrong python version - cannot run')

#TODO - I think that this path append is to allow the template engine to find the template files
#       at ./config/template.  If the template engine is abandoned then this
#       append can go away.
# Add the path to the location of the configuration files.  
#
from sys import exc_info, exit, path
from python.data_file_paths import configuration_directory_location
path.append(configuration_directory_location)

from python.args import get_args
from python.initialize import initialize
from python.logger import get_top_level_logger
from python.utilities.main import execute_utility
from python.main import execute_main
from python.verify_config_files import verify_config_file

# Assign rotating file handler to fopd logger. 
# For now assumed the device name is 'fopd'. Later on it will
# be changed to the value specified in the configuration directory
device_name = 'fopd'
logger = get_top_level_logger(device_name)

# Process the command line args
args = get_args()

# If the user has specifed a utility then run it and then exit.
if args.utility:
    execute_utility(args, device_name)
    # exit normally
    exit(0)

# Check for initialization items in the system_state file.
try:
    initialization_performed = initialize(device_name)
except:
    # exit with error
    exit('initialization error -  cannot run')

if initialization_performed:
    # It is assumed that the fopd must restart itself after
    # any initializations so exit and wait for systemd to
    # re-start the service.
    exit(0)

# Check that the configuration file is present and then load it.
if not verify_config_file():
    # exit with error
    exit('no configuration file - cannot run')

# If you've gotten this far then all preliminaries (e.g. initialization and 
# system checks are successfully done so go ahead and run forever as a 
# fopd.
try:
    result = execute_main(args, device_name)
except:
    # exit with error
    exit('fopd exiting on exception: {}{}'.format(exc_info()[0], exc_info()[1]))

# exit with the code returned by execute_main
exit(result)
