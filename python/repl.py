from getpass import getpass
from logging import getLogger
from sys import exc_info

logger = getLogger('mvp.' + __name__)

from config.config import enable_mqtt, device_name

def get_passphrase():

    #- If mqtt is enabled then ask the user for the passphrase.
    #- if enable_mqtt == True:
        return getpass("Enter your passphrase: ")
    #- else:
    #-    return None

def repl(app_state):

    print('Enter: (help) to see a list of available commands.')

    while True:
       
       try:
          # TBD: Need to sanitize the name to guard against shell attack.
          cmd = input(device_name + ':')
          if cmd == '(help)':
             print('(help) -> display this help message.')
             print('(exit) -> exit this program.')

          elif cmd == '(exit)':
             app_state['stop'] = True
             logger.info('shutting down')
             print('shutting down, please wait a few seconds.')
             break

          elif cmd[:3] == '(p ':
              try:
                 # Need to sandbox the python interpretter as much as possible. Also maybe 
                 # strip out the lispy stuff and go all python.:w
                 
                 eval(cmd[3:-1], app_state)
              except:
                  logger.error('python command: {}, {}, {}'.format(cmd[3:-1], exc_info()[0], exc_info()[1]))
          else:
             print('unknown command. Enter: (help) to see a list of available commands.')
       except:
           logger.error('repl: {}, {}'.format(exc_info()[0], exc_info()[1]))
           app_state['stop'] = True
           break
