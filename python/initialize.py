from json import load, dump
from logging import DEBUG, INFO
from sys import exc_info
from os import path

from python.logger import get_top_level_logger
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


def initialize():

    global fopd_state

    logger = get_top_level_logger('fopd')
    logger.setLevel(DEBUG)

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
              for index in completed_item_indexes:
                  print(index)
                  # TODO: need to remove completed items. the below two methods don't work
                  #       because afte the first pop the arrya is smaller and thus
                  #       the indexes are all wrong.
                  #       Instead rebuild the list without the completed items.
                  # del fopd_state['pending_initialization'][index]
                  #fopd_state['pending_initialization'].pop(index)
              logger.info('ending init list: {}'.format(fopd_state['pending_initialization']))
              """+
              # write the fopd state with completed initializations removed.
              
              f.truncate(0)
              f.seek(0)
              dump(fopd_state, f)
              """
           except:
              msg = 'cannot load and parse state file {}, {}, {}.'.format(state_file_path, exc_info()[0], exc_info()[1])
              logger.error(msg)
              raise Exception('initialization error')

    return True 
