# Evaluate Python Fire https://github.com/google/python-fire.  It generates CLI's for
# Python objects.
#

from getpass import getpass
from logging import getLogger
import re
from sys import exc_info

logger = getLogger('mvp.' + __name__)

from config.config import enable_mqtt, device_name, system

def get_passphrase():

    #- If mqtt is enabled then ask the user for the passphrase.
    #- if enable_mqtt == True:
        return getpass("Enter your passphrase: ")
    #- else:
    #-    return None

def help():
    
    return """\
    sys.help() - displays this page.
    sys.exit() - stop the mvp program.
    sys.dir() - show all available resources\n
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

def repl(app_state):

    print('Enter: sys.help() to see a list of available commands.')

    app_state['sys'] = {}
    app_state['sys']['help'] = help
    app_state['sys']['exit'] = make_exit_mvp(app_state)
    app_state['sys']['dir'] = sys_dir 
    
    repl_globals = {'__builtins__':None, 'dir':dir}

    while not app_state['stop']:
       
        # TBD: Need to sanitize the name to guard against shell attack.
        cmd = input(device_name + ': ')
        
        """
        # Need to add checking so that all commands are of the form foo.bar(args)
        # you could also make this part an interpreter so that args could be evaluated
        # as foo.bar(yet more args) also.
        #
        cmd_parts = cmd.split('.')
        if len(cmd_parts) != 2:
            print('cmds must be of the form foo.bar(args)')
            continue

        f_and_a = cmd_parts[1].split('(')
        if len(f_and_a) != 2:
            print('cmds must be of the form foo.bar(args)')
            continue

        dot_cmd = "cmds['" + cmd_parts[0] + "']" + "['" + f_and_a[0] + "']" + "(" + f_and_a[1] 
        """

        try:
            # Need to sandbox the python interpretter as much as possible. Also maybe 
            # strip out the lispy stuff and go all python.:w
         
            #- result = eval)(dot_cmd, repl_globals, app_state)
            print(trans_cmds(cmd))
            result = eval(trans_cmds(cmd), repl_globals, app_state)
            if result != None:
                print(result)

        except:
            print('command error. enter sys.help() for help')
            logger.error('python command: {}, {}, {}'.format(cmd, exc_info()[0], exc_info()[1]))



