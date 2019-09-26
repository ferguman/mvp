from json import load, dump
from logging import getLogger, DEBUG, INFO
from sys import exc_info
from os import path

#- from python.logger import get_top_level_logger

from python.data_file_paths import state_directory_location
from python.utilities.main import execute_utility

fopd_state = {}

"""-
{
   "pending_initialization": [
      {"cmd":"create_private_key", "args":{"mode":"auto"}},
      {"cmd":"reset_couchdb_passwords", "args":{"silent":"true"}}
   ]
}
"""

def process_init_item(item, logger):

    item['silent'] = True
    execute_utility(item, arg_source='dictionary')


def initialize(device_name):

    global fopd_state

    #- logger = get_top_level_logger('fopd')
    #- logger.setLevel(DEBUG)
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
                  result = process_init_item(item, logger)
                  if result == 'OK':
                     completed_item_indexes.append(index)
                  else:
                     # raise Exception('initializaiton error in {}'.format(item)) 
                     break

              """-
              #- if len(completed_item_indexes) > 0:
              if len(completed_item_indexes) == len(fopd_state['pending_initialization']):
                  initialization_completed = True
                  logger.info('All initializations were performed, so this instance of fopd will exit.')
              else:
                  initialization_completed = False 
                  logger.info('No Initializations were performed.')
              """

              # Remove the completed items from the state file so that on future starts
              # they will not be applied.
              new_init_list = []
              for index, item in enumerate(fopd_state['pending_initialization']):
                  if not index in completed_item_indexes:
                      new_init_list.append(item)
              fopd_state['pending_initialization'] = new_init_list
              logger.info('ending init list: {}'.format(fopd_state['pending_initialization']))

              """+
              # write the fopd state with completed initializations removed.
              
              f.truncate(0)
              f.seek(0)
              dump(fopd_state, f)
              """

              #- return initialization_completed
              return True 
           except:
              msg = 'cannot load and parse state file {}, {}, {}.'.format(state_file_path, exc_info()[0], exc_info()[1])
              logger.error(msg)
              raise Exception('initialization error')
    else:
        raise Exception('initialization error - no state file found.')
