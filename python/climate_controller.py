from os import path, getcwd
from sys import exc_info
from time import sleep, time
import datetime
import json
import time

from python.logData import logDB
from python.logger import get_sub_logger 

logger = get_sub_logger(__name__)

# State variables:
# 1) recipe
# 2) run_mode: 'on' or 'off'
climate_state = {} 

def load_recipe_file(rel_path):

    climate_state['recipe'] = None

    recipe_path = getcwd() + rel_path
    logger.debug('opening recipe file: {}'.format(recipe_path))

    if path.isfile(recipe_path):
        logger.debug('found recipe file')

        with open(recipe_path) as f:
            try:
                recipe = json.load(f)
                climate_state['recipe'] = recipe
            except:
                logger.error('cannot parce recipe file.')
        
    else:
        logger.debug('no recipe file found. the climate controller cannot run without a recipe file.')

def load_state_file(rel_path):


    state_file_path = getcwd() + rel_path
    logger.debug('opening climate state file: {}'.format(state_file_path))

    if path.isfile(state_file_path):
        logger.debug('found state file - will load it')
        
        with open(state_file_path) as f:
            try:
                global climate_state
                climate_state = json.load(f)
            except:
                logger.error('cannot load state file.')
        
    else:
        logger.debug('no state file found. The climate controller will be set to off.')

def write_state_file(rel_path, update_interval):

    if time.time() >= climate_state['last_state_file_update_time'] + update_interval:

        # Go ahead and log the update time even though the file write is not done. This way
        # you want bang on the file system over and over in the presence of errors.
        climate_state['last_state_file_update_time'] = time.time()
       
        try:
            state_file_path = getcwd() + rel_path
            logger.info('writing climate state file {}'.format(state_file_path))

            with open(state_file_path, 'w') as outfile:
                    json.dump(climate_state, outfile)
        except:
            logger.error('error encountered while writing state file: {}{}'.format(exc_info()[0], exc_info()[1]))


def make_help(prefix):

    def help():

        s =     '{}.help()                    - Displays this help page.\n'.format(prefix)
        s = s + '{}.state()                   - Show climate controller state.\n'.format(prefix)
        
        return s

    return help

def show_state():

    try:
        s =     'Mode:  {}\n'.format(climate_state['run_mode'])  

        if climate_state['recipe_start_time'] != None:
            st = datetime.datetime.fromtimestamp(climate_state['recipe_start_time']).isoformat()
        else:
            st = None
        s = s + 'Recipe start time: {}\n'.format(st)

        s = s + 'Current minute: {}\n'.format(climate_state['cur_min'])
        s = s + 'Phase: {}\n'.format(climate_state['current_phase'])   
        s = s + 'Last state file write: {}\n'.format(datetime.datetime.fromtimestamp(
                                                     climate_state['last_state_file_update_time']).isoformat())
        return s

    except:
        logger.error('show_state command {}{}'.format(exc_info()[0], exc_info()[1]))


def init_state(args):

    # Initialize the climate controller state - this stuff will get replaced
    # if there is a state file to load
    climate_state['run_mode'] = 'off'
    climate_state['current_phase'] = None
    climate_state['recipe_start_time'] = None
    # make sure the state has a recipe in case there is no state file.
    load_recipe_file(args['default_recipe_file'])

    # See if there is previous state in a state file  and load it if you have it, otherwise
    # create a state file so it's there the next time we reboot.
    load_state_file(args['state_file'])
    climate_state['last_state_file_update_time'] = time.time()
    
    climate_state['cur_min'] = datetime.datetime.now().minute

    # set_todays_cycle()

def check_lights():
    pass

    # if we are in a cycle
        # if the cycle has light instrucionts
            # step through each light instruciont
            # if the current light instruciton is on then
               # app_state['sys']['cmd'](args['light_on_cmd'])
            # if the current light instruciotn is off then
               # app_state['sys']['cmd'](args['light_off_cmd'])
       

def start(app_state, args, barrier):

    logger.setLevel(args['log_level'])
    logger.info('starting climate controller thread')

    # Inject this resources commands into app_state
    app_state[args['name']] = {}
    app_state[args['name']]['help'] = make_help(args['name']) 
    app_state[args['name']]['state'] = show_state

    init_state(args)

    # Don't proceed until all the other resources are available.
    barrier.wait()    

    while not app_state['stop']:

       #update_phase_and_cycle()

       if climate_state['run_mode'] == 'on': 

           cur_min = datetime.datetime.now().minute
           if cur_min > climate_state['cur_min']:
               climate_state['cur_min'] = cur_min

               # if we have not updated this minute
               check_lights()

           #check_air_flush()
           #check_air_temperature()

       write_state_file(args['state_file'], args['state_file_write_interval'])

       sleep(1)

    write_state_file(args['state_file'], args['state_file_write_interval'])
    logger.info('exiting climate controller thread')
