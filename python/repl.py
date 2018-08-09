from getpass import getpass
from logging import getLogger
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
    
     return """
     all commands must be of the form foo.bar(args). args may be blank.\n
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

def make_sys_dir(app_state):

    def sys_dir():
        s = ''
        for r in system['resources']:
            s = s + 'name: {}, implementation: {}\n'.format(r['args']['name'], r['imp'])
        return s

    return sys_dir

def repl(app_state):

    print('Enter: sys.help() to see a list of available commands.')

    app_state['cmds']['sys'] = {}
    app_state['cmds']['sys']['help'] = help
    app_state['cmds']['sys']['exit'] = make_exit_mvp(app_state)
    app_state['cmds']['sys']['dir'] = make_sys_dir(app_state)
    
    repl_globals = {'__builtins__':None, 'dir':dir}

    while not app_state['stop']:
       
        # TBD: Need to sanitize the name to guard against shell attack.
        cmd = input(device_name + ': ')
        
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
        
        try:
            # Need to sandbox the python interpretter as much as possible. Also maybe 
            # strip out the lispy stuff and go all python.:w
         
            result = eval(dot_cmd, repl_globals, app_state)
            if result != None:
                print(result)

        except:
            print('command error. enter sys.help() for help')
            logger.error('python command: {}, {}, {}'.format(cmd, exc_info()[0], exc_info()[1]))
