# TBD: Need to write the state file out whenever a change is made that makes this necessary (such as someone turning
#      a recipe on or off.  Add this functionality. Currenlty the state file is written out every state_file_write_interval
#      seconds and when the program gracefully exits.

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

def write_state_file(rel_path, update_interval, force):

    if force or (time.time() >= climate_state['last_state_file_update_time'] + update_interval):

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

        s =     '{}.help()                         - Displays this help page.\n'.format(prefix)
        s = s + "{}.cmd('start'|'stop', options)   - Execute the given command.\n".format(prefix)
        s = s + "                                    {}.cmd('start', day_index=n) - start recipe on the designated day (0 based). If no day_index is supplied then start on day 0.\n".format(prefix)
        s = s + "                                    e.g. {}.cmd('start', day_index=2) to start recipe on 3rd day.\n".format(prefix)
        s = s + "                                    {}.cmd('stop') - stop the current recipe.\n".format(prefix)
        s = s + '{}.state()                        - Show climate controller state.\n'.format(prefix)
        
        return s

    return help

def show_recipe():

    if climate_state['recipe'] != None:
        return climate_state['recipe']
    else:
        return None 

def show_state():

    try:
        s =     'Mode:  {}\n'.format(climate_state['run_mode'])  

        if climate_state['recipe'] != None:
            s = s + 'Recipe id: {}\n'.format(climate_state['recipe']['id'])
        else:
            s = s + 'Recipe id: None\n'

        if climate_state['recipe_start_time'] != None:
            s = s + 'Recipe start time: {}\n'.format(datetime.datetime.fromtimestamp(climate_state['recipe_start_time']))
        else:
            s = s + 'Recipe start time: None\n'

        s = s + 'Current day index: {}\n'.format(climate_state['cur_day'])
        s = s + 'Current hour: {}\n'.format(climate_state['cur_hour'])
        s = s + 'Current minute: {}\n'.format(climate_state['cur_min'])
        if climate_state['recipe'] != None and climate_state['cur_phase_index'] != None:
            s = s + 'Current phase: {}\n'.format(climate_state['recipe']['phases'][climate_state['cur_phase_index']]['name'])   

        s = s + 'Current phase index: {}\n'.format(climate_state['cur_phase_index'])   

        s = s + 'Grow light on: {}\n'.format(climate_state['grow_light_on'])
        if climate_state['grow_light_last_on_time'] != None:
            s = s + 'Last grow light on time: {}\n'.format(datetime.datetime.fromtimestamp(climate_state['grow_light_last_on_time']))
        else:
            s = s + 'Last grow light on time: None\n'

        if climate_state['grow_light_last_off_time'] != None:
            s = s + 'Last grow light off time: {}\n'.format(datetime.datetime.fromtimestamp(climate_state['grow_light_last_off_time']))
        else:
            s = s + 'Last grow light off time: None\n'

        s = s + 'Vent fan on: {}\n'.format(climate_state['vent_fan_on'])
        if climate_state['vent_last_on_time'] != None:
            s = s + 'Last vent fan on time: {}\n'.format(datetime.datetime.fromtimestamp(climate_state['vent_last_on_time']))
        else:
            s = s + 'Last vent fan on time: None\n'

        s = s + 'Air heater on: {}\n'.format(climate_state['air_heater_on'])
        s = s + 'Air temperature: {}\n'.format(climate_state['cur_air_temp'])
        s = s + 'Air heater last on time: {}\n'.format(climate_state['air_heater_last_on_time'])
        s = s + 'Air heater last off time: {}\n'.format(climate_state['air_heater_last_off_time'])

        s = s + 'Last state file write: {}\n'.format(datetime.datetime.fromtimestamp(
                                                     climate_state['last_state_file_update_time']).isoformat())
        return s

    except:
        logger.error('show_state command {}{}'.format(exc_info()[0], exc_info()[1]))
        return "Error - can't show stat"

def cmd(*args, **kwargs):
   
    if len(args) == 1:
        if args[0] == 'start':

            if 'day_index' in kwargs:
                climate_state['cur_day'] = kwargs['day_index']
            else:
                climate_state['cur_day'] = 0

            climate_state['run_mode'] = 'on'
            climate_state['recipe_start_time'] = (datetime.datetime.now() - datetime.timedelta(days=climate_state['cur_day'])).timestamp()
            return 'OK'
        elif args[0] == 'stop':
            climate_state['run_mode'] = 'off'
            climate_state['recipe_start_time'] = None
            return 'OK'
        else:
            return "illegal command: {}. please specify 'start' or 'stop'".format(args[0])
    else:
        return "you must supply a cmd (e.g. 'start')"


def init_state(args):

    # Initialize the climate controller state - this stuff will get replaced
    # if there is a state file to load
    climate_state['run_mode'] = 'off'
    climate_state['cur_phase_index'] = None
    climate_state['recipe_start_time'] = None
    # make sure the state has a recipe in case there is no state file.
    load_recipe_file(args['default_recipe_file'])

    # See if there is previous state in a state file  and load it if you have it, otherwise
    # create a state file so it's there the next time we reboot.
    load_state_file(args['state_file'])
    climate_state['last_state_file_update_time'] = time.time()


    now = datetime.datetime.now()
    climate_state['cur_min'] = now.minute
    climate_state['cur_hour'] = now.hour
    if climate_state['recipe_start_time'] != None:
        climate_state['cur_day'] = (now - datetime.datetime.fromtimestamp(climate_state['recipe_start_time'])).days
    else:
        climate_state['cur_day'] = None
        
    climate_state['grow_light_on'] = False
    climate_state['grow_light_last_on_time'] = None
    climate_state['grow_light_last_off_time'] = None

    climate_state['vent_fan_on'] = False
    climate_state['vent_last_on_time'] = None

    climate_state['air_heater_on'] =  False
    climate_state['cur_air_temp'] = None
    climate_state['air_heater_last_on_time'] = None
    climate_state['air_heater_last_off_time'] = None

    # climate_state['cur_time'] = 0 
    climate_state['last_log_time'] = 0
    climate_state['log_cycle'] = False

# step_name -> e.g. light_intensity, air_fush
#
def get_current_recipe_step_value(step_name):

    value = None

    try:
        times = climate_state['recipe']['phases'][climate_state['cur_phase_index']]['step'][step_name]
        if len(times) > 0:
            
            for t in times:

                past_start = False
                lt_end = False
               
                # accept times as either integers (i.e the hour) or strings (e.g. hh:mm)
                if isinstance(t['start_time'], int):
                    start = [int(t['start_time']), int((t['start_time'] - int(t['start_time'])) * 60)]
                else:
                    start = t['start_time'].split(':')

                if start[0] <= climate_state['cur_hour']: 
                    if len(start) > 1:
                        if start[1] <= climate_state['cur_min']:
                            past_start = True
                        else:
                            past_start = False
                    else:
                        past_start = True 

                if isinstance(t['end_time'], int):
                    end = [int(t['end_time']), int((t['end_time'] - int(t['end_time'])) * 60)]
                else:
                    end = t['end_time'].split(':')
                
                if len(end) == 1:
                    if end[0] > climate_state['cur_hour']: 
                        lt_end = True
                    else:
                        lt_end = False
                else:
                    if (end[0] > climate_state['cur_hour']) or\
                       (end[0] == climate_state['cur_hour'] and end[1] > climate_state['cur_min']):
                            lt_end = True
                    else:
                        lt_end = False 

                if past_start and lt_end:
                    value = t['value']

                # logger.info('start: {}, end: {}, past_start: {}, lt_end: {}'.format(start, end, past_start, lt_end))

        else:
            if climate_state['log_cycle']:
                logger.warning('There are no recipe steps for: {}.  Why?'.format(step_name))

    except:
        logger.error('failed looking for step value: {}, {}, {}'.format(step_name, exc_info()[0], exc_info()[1]))

    return value

# step_name -> e.g. light_intensity, air_fush
# value names -> tuple list of value names to return
#
def get_current_recipe_step_values(step_name, value_names):

    values = None 

    try:
        times = climate_state['recipe']['phases'][climate_state['cur_phase_index']]['step'][step_name]
        if len(times) > 0:
            
            for t in times:

                past_start = False
                lt_end = False
               
                # accept times as either integers (i.e the hour) or strings (e.g. hh:mm)
                if isinstance(t['start_time'], int):
                    start = [int(t['start_time']), int((t['start_time'] - int(t['start_time'])) * 60)]
                else:
                    start = t['start_time'].split(':')

                if start[0] <= climate_state['cur_hour']: 
                    if len(start) > 1:
                        if start[1] <= climate_state['cur_min']:
                            past_start = True
                        else:
                            past_start = False
                    else:
                        past_start = True 

                if isinstance(t['end_time'], int):
                    end = [int(t['end_time']), int((t['end_time'] - int(t['end_time'])) * 60)]
                else:
                    end = t['end_time'].split(':')
                
                if len(end) == 1:
                    if end[0] > climate_state['cur_hour']: 
                        lt_end = True
                    else:
                        lt_end = False
                else:
                    if (end[0] > climate_state['cur_hour']) or\
                       (end[0] == climate_state['cur_hour'] and end[1] > climate_state['cur_min']):
                            lt_end = True
                    else:
                        lt_end = False 

                if past_start and lt_end:

                    values = {}

                    for vn in value_names:
                        if vn in t:
                            values[vn] = t[vn]
                        else:
                            logger.warning('cannot find value {} in step {}.'.format(vn, step_name))

                # logger.info('start: {}, end: {}, past_start: {}, lt_end: {}'.format(start, end, past_start, lt_end))

        else:
            if climate_state['log_cycle']:
                logger.warning('There are no recipe steps for: {}.  Why?'.format(step_name))

    except:
        logger.error('failed looking for step values: {}, {}, {}'.format(step_name, exc_info()[0], exc_info()[1]))

    return values

def check_lights(controller):
    
    value = get_current_recipe_step_value('light_intensity')
    light_on = None

    if value != None:
        if value  == 1:
            if not climate_state['grow_light_on']: 
                light_on = True
        else:
            if climate_state['grow_light_on']:
                light_on = False 
    else:
        if climate_state['grow_light_on']:
            light_on = False 

    if light_on != None:
        if light_on:
            climate_state['grow_light_on'] = True
            climate_state['grow_light_last_on_time'] = climate_state['cur_time'] 
            controller['cmd']('on', 'grow_light') 
        else:
            climate_state['grow_light_on'] = False 
            climate_state['grow_light_last_off_time'] = climate_state['cur_time']
            controller['cmd']('off', 'grow_light')


def check_vent_fan(controller):

    values = get_current_recipe_step_values('air_flush', ('interval', 'duration'))
    fan_on = None

    #logger.debug('vent_fan_on: {}, vent_last_on_time: {}, cur_time: {}, duration: {}, interval: {}'.format(climate_state['vent_fan_on'], climate_state['vent_last_on_time'], climate_state['cur_time'], values['duration'], values['interval']))

    if values != None and climate_state['vent_last_on_time'] != None:
        if climate_state['vent_fan_on'] and climate_state['cur_time'] - climate_state['vent_last_on_time'] > 60 * values['duration']:
            fan_on = False
        if not climate_state['vent_fan_on'] and\
               climate_state['cur_time'] - climate_state['vent_last_on_time'] > 60 * values['interval']:
            fan_on = True
    elif values != None and climate_state['vent_last_on_time'] == None:
        # Assume this is a startup state.  There are recipe values for the flush flan but no history on the flushing so go 
        # ahead and start a flush cycle.
        fan_on = True
    else:
        # There are no recipe values for flushing so leave the fan off.
        fan_on = False

    if fan_on != None:
        if fan_on:
            climate_state['vent_fan_on'] = True
            climate_state['vent_last_on_time'] = climate_state['cur_time']
            controller['cmd']('on', 'vent_fan') 
            logger.info('turning vent fan on') 
        else:
            climate_state['vent_fan_on'] = False
            controller['cmd']('off', 'vent_fan') 
            logger.info('turning vent fan off') 


def check_air_temperature(controller):

    values = get_current_recipe_step_values('air_temperature', ('low_limit', 'high_limit'))
    heater_on = None

    if values != None:
        if values ['high_limit'] - values['low_limit'] >= 1:
            if climate_state['cur_air_temp'] != None:
                if climate_state['cur_air_temp'] > values['high_limit'] and not climate_state['air_heater_on']:
                    heater_on = True
                elif climate_state['cur_air_temp'] <= values['high_limit'] and climate_state['air_heater_on']:
                    heater_on = False
            else:
                logger.warning('No air temperature avaialble. Will turn heater off.')
                heater_on = False 
        else:
            if climate_state['log_cycle']: 
                logger.error('illegal values for high and low limits. high limit must be at least 1 degrees higher than' +\
                             ' low limit.')

    else:
        logger.info('no temperature instructions found')
        heater_on = False

    # Don't run the heater for more than 30 minutes.
    if climate_state['air_heater_on'] and climate_state['cur_time'] - climate_state['air_heater_last_on_time'] > 60 * 30:
        heater_on = False

    if heater_on != None:
        if heater_on:
            # Don't turn the heater on more than once per minute.
            if climate_state['cur_time'] - climate_state['air_heater_last_on_time'] >= 60: 
                logger.info('turning the air heater on')
                climate_state['air_heater_on'] = True
                climate_state['air_heater_last_on_time'] = climate_state['cur_time']
                controller['cmd']('air_heater', 'on')
        else:
            logger.info('turning the air heater off')
            climate_state['air_heater_on'] = False 
            climate_state['air_heater_last_off_time'] = climate_state['cur_time']
            controller['cmd']('air_heater', 'off')


def get_phase_index(cur_day_index, phases):

    try:

        rcp_day_index = 0

        for i in range(0, len(phases)):
            
            rcp_phase_cycles = phases[i]['cycles']

            if cur_day_index >= rcp_day_index and cur_day_index < rcp_day_index + rcp_phase_cycles: 

                return i

            else:
                rcp_day_index = rcp_day_index + cur_cycles

        logger.error('the current recipe does not apply to today. It may be over.')
        return None

    except:
        logger.error('cannot update phase index: {}, {}'.format(exc_info()[0], exc_info()[1]))
        return None

def update_climate_state(min_log_period, controller):

    now = datetime.datetime.now()
    
    climate_state['cur_min'] = now.minute
    climate_state['cur_hour'] = now.hour
    
    if climate_state['recipe_start_time'] != None:
        climate_state['cur_day'] = (now - datetime.datetime.fromtimestamp(climate_state['recipe_start_time'])).days
    else:
        climate_state['cur_day'] = None

    climate_state['cur_phase_index'] = get_phase_index(climate_state['cur_day'], climate_state['recipe']['phases'])

    climate_state['cur_time'] = time.time()   # Return the time in seconds since the epoch as a floating point number.

    if climate_state['cur_time']  - climate_state['last_log_time'] >= min_log_period:   
        climate_state['last_log_time'] = climate_state['cur_time']
        climate_state['log_cycle'] =  True
    else:
        climate_state['log_cycle'] = False

    at = controller['get']('air_temp')['value']
    try:
        climate_state['cur_air_temp'] = float(at)
    except:
        if climate_state['log_cycle']:
            logger.warning('cannot read air temperature. value returned by source is {}'.format(at))

    # logger.info('cur_time {}, last_log_time: {}, log_cycle: {}'.format(climate_state['cur_time'], 
    #             climate_state['last_log_time'], climate_state['log_cycle']))

def start(app_state, args, barrier):

    logger.setLevel(args['log_level'])
    logger.info('starting climate controller thread')

    # Inject this resources commands into app_state
    app_state[args['name']] = {}
    app_state[args['name']]['help'] = make_help(args['name']) 
    app_state[args['name']]['state'] = show_state
    app_state[args['name']]['recipe'] = show_recipe
    app_state[args['name']]['cmd'] = cmd

    init_state(args)

    # Don't proceed until all the other resources are available.
    barrier.wait()    

    while not app_state['stop']:

       if climate_state['run_mode'] == 'on': 

           update_climate_state(args['min_log_period'], app_state['mc'])

           # TBD - need to make 'mc' configurable from config file.
           check_lights(app_state['mc'])

           check_vent_fan(app_state['mc'])
           
           check_air_temperature(app_state['mc'])

       write_state_file(args['state_file'], args['state_file_write_interval'], False)

       sleep(1)

    write_state_file(args['state_file'], args['state_file_write_interval'], True)
    logger.info('exiting climate controller thread')
