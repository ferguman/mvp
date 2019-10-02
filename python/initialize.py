from json import load, dump
from logging import getLogger, DEBUG, INFO
from sys import exc_info
from os import path

#- from python.logger import get_top_level_logger

from python.data_file_paths import state_directory_location
from python.utilities.main import execute_utility

fopd_state = {}

"""
Add initializations commands to the pending_initialization dictionary
in the system_state file.  The text below contains all the current
(as of 10/3/2019) initalization commands.

Some commands write new values to Python files. Others may 
read those values.  All commands run within the scope of the
initial pre-written values that existed when the fopd.py loaded by 
the Python environment and thus does not reflect the newly written 
values. So a flag named reset_after is provided in the argument list
to commands. Any command writting a Python file should set this flag
to true so that the fopd.py program exits after that command. Then
Subsequent inovakations of fopd.py will run an pick up after the
last completed initialiation command.

{
   "pending_initialization": [
      {"cmd":"create_private_key", "args":{"mode":"auto", "reset_after":true}},
      {"cmd":"reset_couchdb_passwords", "args":{"reset_after":false}}
   ]
}
"""

def process_init_item(item, logger):

    item['args']['silent'] = True
    return execute_utility(item, arg_source='dictionary')


def initialize(device_name):

    global fopd_state

    logger = getLogger(device_name + '.init')
    logger.info('############## initializing fopd device  ################')

    global fopd_state

    state_file_path = path.join(state_directory_location, 'system_state.json')
    logger.info('opening state file: {}'.format(state_file_path))

    if path.isfile(state_file_path):
        logger.debug('found state file')

        with open(state_file_path, 'r+') as f:
           try:
              fopd_state = load(f)
              logger.info('beginning init list: {}'.format(fopd_state['pending_initialization']))

              if len(fopd_state['pending_initialization']) == 0:
                 logger.info('There are no initializations in the fopd state file.')
                 return False 

              completed_item_indexes = []

              for index, item in enumerate(fopd_state['pending_initialization']):
                  if process_init_item(item, logger):
                     completed_item_indexes.append(index)
                     logger.info('reset_after: {}'.format(item['args']['reset_after']))
                     if item['args']['reset_after']:
                         break
                  else:
                     # the current item failed so stop initializing. 
                     break

              # Remove the completed items from the state file so that on future starts
              # they will not be applied.
              new_init_list = []
              for index, item in enumerate(fopd_state['pending_initialization']):
                  if not index in completed_item_indexes:
                      new_init_list.append(item)
              fopd_state['pending_initialization'] = new_init_list
              logger.info('ending init list: {}'.format(fopd_state['pending_initialization']))

              # write the fopd state with completed initializations removed.
              f.truncate(0)
              f.seek(0)
              dump(fopd_state, f)

              return True 
           except:
              msg = 'cannot load and parse state file {}, {}, {}.'.format(state_file_path, exc_info()[0], exc_info()[1])
              logger.error(msg)
              raise Exception('initialization error')
    else:
        raise Exception('initialization error - no state file found.')
