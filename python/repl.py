# TODO: Evaluate Python Fire https://github.com/google/python-fire.  It generates CLI's for
# Python objects.

from getpass import getpass
from sys import exc_info
from threading import Lock
from time import sleep
import re

from flask import request

from python.logger import get_sub_logger 

logger = get_sub_logger(__name__)

cmd_lock = Lock()

def help():
    
    return """\
    sys.help() -   displays this page.
    sys.exit() -   stop the fopd program.
    sys.dir() -    show all available resources.
    sys.cmd(cmd) - run a command. Note: that if a command calls this command then the system will lock
                   forever waiting for the first call to finish.  This command is not reentrant. Also
                   if you call this command from the command prompt then the sytem will lock forever. This
                   command is meant for resources such as an MQTT client to use.\n

    In order to access the help for each resource enter: resource_name.help() where
    resource_name is the name of the resource. Enter sys.dir() to see a list of 
    available resources on your system. Example: camera.help().
    """

def make_exit(app_state):

    def exit_cmd():
         logger.info('shutting down')
         app_state['stop'] = True
         return 'shutting down, please wait a few seconds.'

    return exit_cmd

def make_sys_dir_cmd(system):

    def sys_dir():
        s = ''
        for r in system['resources']:
            s = s + '    name: {}, implementation -> {}\n'.format(r['args']['name'], r['imp'])
        return s

    return sys_dir

cmd_re = re.compile(r'(([a-z_]{1,25}\.){0,5})[a-z_]{1,25}\(')
cmd_parts_re = re.compile(r'([a-z_]{1,25}\.)|([a-z_]{1,25}\()')

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

    # Python docs for re.sub(func, str): Return the string obtained by replacing the leftmost non-overlapping 
    # occurrences of the regex pattern in str by the values obtained by applying func to the regex match strings.
    #
    # 1st -> start with a string like:  abc.def.ghi(stuff)
    # 2nd -> find the part up to the paranthesis, eg. abc.def.ghi(
    # 3rd -> replace the first sub-part (e.g. abc.) with everything but the dot (e.g. abc)
    # 4th -> replace the other sub parts (e.g. def. or ghi() with ['sub-part'] (e.g. ['def'] or ['ghi']
    # 5th -> add the parentheses back in (e.g. abc['def']['ghi']( )
    # 6th -> return the modified string (e.g. abc['def']['ghi'](stuff) )
    #
    return cmd_re.sub(trans_cmd, input_str)

def make_run_cmd(repl_globals, app_state):

    def run_cmd(cmd):
       
        # Currently the system implements functions that cause this function to be re-entered. For
        # example run the camera.snap() command from the terminal. So this function cannot lock or
        # it will deadlock on the 2nd entry.
        
        try:
            logger.info('will evaluate {}'.format(trans_cmds(cmd)))
            
            # eval(exp, globals, locals) -> The exp argument is parsed and evaluated as a Python expression 
            # (technically speaking, a condition list) using the globals and locals dictionaries as global
            # and local namespace.
            # Note that Python appears to parse the cmd string.  For example one can enter sys['help']() and 
            # the Python interpretter will successfully find the app_state['sys']['help'] object which is a
            # function and then will apply the function to the empty argument list. My point is that Python
            # is parsing the input to isolate 'sys' as a symbol that is to be interpretted as a dictionary
            # key to be found in either globals or locals.
            #
            # Note that the repl_globals and app_state only apply to the trans_cmds(cmd) statement resolution.
            #      If cmd is a reference to other functions then those functions run within the context of the 
            #      the already compiled Python code. 
            #      See https://stackoverflow.com/questions/43349334/eval-globals-and-locals-argument-do-not-work-as-expected
            return eval(trans_cmds(cmd), repl_globals, app_state)
        except:
            logger.error('python command: {}, {}, {}'.format(cmd, exc_info()[0], exc_info()[1]))
            return 'command error. enter sys.help() for help'
        finally:
            pass

    return run_cmd

# TODO: See flask.pocoo.org/snippets/67/ and flask.pocoo.org/docs/1.0/reqcontext.
#       As of 9/30 this code returns No shutdown function found. The docs say this
#       reset stuff only works on the development server. I think my testing was done
#       in producton mode. Need to retest in development mode.
#
def make_shut_down_werkzeug(app_state):
    return None 
    """ -
    def shut_down_werkzeug():
        with app_state['sys']['flask_app'].test_request_context('/bogus'):
            func = request.environ.get('werkzeug.server.shutdown')
            if func is None:
                return 'No shutdown function found'
            else:
                return 'found a shutdown function'

    return shut_down_werkzeug
    """


def start(app_state, silent_mode, barrier, start_cmd=None):

    # repl_globals = {'__builtins__':None, 'logger':logger}
    repl_globals = {'__builtins__':None}

    app_state['sys']['cmd'] = make_run_cmd(repl_globals, app_state) 

    app_state['sys']['help'] = help
    app_state['sys']['exit'] = make_exit(app_state)
    app_state['sys']['dir'] = make_sys_dir_cmd(app_state['system']) 
    app_state['sys']['sdw'] = make_shut_down_werkzeug(app_state)

    # Let the system know that you are good to go.
    if barrier:
        try:
            if not silent_mode:
                print('Waiting for system to initialize...')
            barrier.wait()
        except Exception as err:
            # assume a broken barrier
            logger.error('barrier error: {}'.format(str(err)))
            app_state['stop'] = True

    if start_cmd:
        if silent_mode:
           return app_state['sys']['cmd'](start_cmd)
        else:
           print(app_state['sys']['cmd'](start_cmd))

    if not app_state['stop']:    
        print('Enter: sys.help() to see a list of available commands.')
    
    while not app_state['stop']:

        # Listen for commands from the shell if enabled, otherwise wait to be stopped.
        if not silent_mode:
            # TBD: Need to sanitize the name to guard against shell attack.
            cmd = input(app_state['config']['device_name'] + ': ')
            print(app_state['sys']['cmd'](cmd))
        else:
            # TODO - I think one can just return at this point. No need to keep the thread safe, 
            #        but wait, things like repl_globals need to stay alive so the command interpretter 
            #        can be invoked from other resources. So maybe I can't kill the thread.
            sleep(1)

    logger.info('command interpretter exiting')
