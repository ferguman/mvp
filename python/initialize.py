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

def process_init_item(item):

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
              completed_item_indexes = []

              for index, item in enumerate(fopd_state['pending_initialization']):
                  process_init_item(item)
                  completed_item_indexes.append(index)

              if len(completed_item_indexes) > 0:
                  initialization_performed = True
                  logger.info('Initializations were performed, so this instance of fopd will exit')
              else:
                  initialization_performed = False 
                  logger.info('No Initializations were performed.')

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

              return initialization_performed
           except:
              msg = 'cannot load and parse state file {}, {}, {}.'.format(state_file_path, exc_info()[0], exc_info()[1])
              logger.error(msg)
              raise Exception('initialization error')
    else:
        raise Exception('initialization error - no state file found.')
