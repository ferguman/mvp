# Evaluate Python Fire https://github.com/google/python-fire.  It generates CLI's for
# Python objects.
#

from getpass import getpass
from sys import exc_info
from threading import Lock
import re

from python.logger import get_sub_logger 

logger = get_sub_logger(__name__)

from config.config import enable_mqtt, device_name, system

cmd_lock = Lock()

def get_passphrase():

    #- If mqtt is enabled then ask the user for the passphrase.
    #- if enable_mqtt == True:
        return getpass("Enter your passphrase: ")
    #- else:
    #-    return None

def help():
    
    return """\
    sys.help() -   displays this page.
    sys.exit() -   stop the mvp program.
    sys.dir() -    show all available resources
    sys.cmd(cmd) - run a command. Note: that if a command calls this command then the system will lock
                   forever waiting for the first call to finish.  This command is not reentrant. Also
                   if you call this command from the command prompt then the sytem will lock forever. This
                   command is meant for resources such as an MQTT client to use.\n

    In order to access the help for each resource enter: resource_name.help() where
    resource_name is the name of the resource. Enter sys.dir() to see a list of 
    available resources on your system. Example: camera.help().
    """

def make_exit_mvp(app_state):

    def exit_mvp():
         app_state['stop'] = True
         logger.info('shutting down')
         return 'shutting down, please wait a few seconds.'

    return exit_mvp

def sys_dir():
    s = ''
    for r in system['resources']:
        s = s + '    name: {}, implementation -> {}\n'.format(r['args']['name'], r['imp'])
    return s

cmd_re = re.compile(r'(([a-z_]{1,20}\.){0,5})[a-z_]{1,20}\(')
cmd_parts_re = re.compile(r'([a-z_]{1,20}\.)|([a-z_]{1,20}\()')

def trans_cmd_part(match):

    if match.start() == 0:
        return match.group()[0:-1]
    else:
        return "['{}']".format(match.group()[0:-1])

def trans_cmd(match):

    global cmd_parts_re
    return "{}(".format(cmd_parts_re.sub(trans_cmd_part, match.group()))

def trans_cmds(input_str):

    global cmd_re
    return cmd_re.sub(trans_cmd, input_str)

def make_run_cmd(repl_globals, app_state):

    def run_cmd(cmd):
        
        # Wait for a lock.
        cmd_lock.acquire()
        
        try:
            # debug print -> print(trans_cmds(cmd))
            return eval(trans_cmds(cmd), repl_globals, app_state)
        except:
            return 'command error. enter sys.help() for help'
            logger.error('python command: {}, {}, {}'.format(cmd, exc_info()[0], exc_info()[1]))
        finally:
            cmd_lock.release()

    return run_cmd

def repl(app_state):

    print('Enter: sys.help() to see a list of available commands.')

    repl_globals = {'__builtins__':None, 'dir':dir}

    global run_cmd
    run_cmd  = make_run_cmd(repl_globals, app_state) 

    app_state['sys'] = {}
    app_state['sys']['help'] = help
    app_state['sys']['exit'] = make_exit_mvp(app_state)
    app_state['sys']['dir'] = sys_dir 
    app_state['sys']['cmd'] = make_run_cmd(repl_globals, app_state) 

    # TBD - considering adding a command: sys.inject(r[resource_name], 'start':'stop')
    #       when in inject mode the system would pass the user input directory to resource 
    #       as in -> ['app_state']['[resource_name]')['cmd'](user input))
    #       This would make it easier to do things like spend time sending and receiving input
    #       from the Arduino serial monitor.

    while not app_state['stop']:
       
        # TBD: Need to sanitize the name to guard against shell attack.
        cmd = input(device_name + ': ')

        print(app_state['sys']['cmd'](cmd))

    logger.info('command line interface exiting')
