# TBD: Need to write the state file out whenever a change is made that makes this necessary (such as someone turning
#      a recipe on or off.  Add this functionality. Currenlty the state file is written out every state_file_write_interval
#      seconds and when the program gracefully exits.

from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL
from os import path, getcwd
from sys import exc_info
from threading import Lock
from time import sleep, time

import datetime
from json import dump, dumps, load 

from python.logData import logDB
from python.logger import get_sub_logger
from python.LogFileEntryTable import LogFileEntryTable

from python.data_file_paths import recipes_directory_location, state_directory_location

# Provide a lock to control access to the climate controller state

#
state_lock = Lock()

logger = get_sub_logger(__name__)

log_entry_table = LogFileEntryTable(60*60)

# State variables:
climate_state = {} 

# Load the recipe file found at rel_path and stick the JSON into climate_state['recipe']
#
def load_recipe_file(rel_path):

    global climate_state

    #- recipe_path = path.join(getcwd() + rel_path) 
    recipe_path = path.join(recipes_directory_location, rel_path) 
    logger.info('loading recipe file: {}'.format(recipe_path))

    if path.isfile(recipe_path):
        logger.debug('found recipe file')

        with open(recipe_path) as f:
            try:
                climate_state['recipe'] = load(f)
                return (True, 'OK')
            except:
                msg = 'cannot load and parse recipe file {}, {}, {}.'.format(recipe_path, exc_info()[0], exc_info()[1])
                logger.error(msg)
    else:
        msg = 'No recipe file found at {}. The climate controller cannot run without a recipe file.'.format(recipe_path)
        logger.error(msg)
       
    climate_state['recipe'] = None
    return (False, msg)
    

def load_state_file(rel_path):

    global climate_state

    #- state_file_path = getcwd() + rel_path
    state_file_path = path.join(state_directory_location, rel_path)
    logger.debug('opening climate state file: {}'.format(state_file_path))

    if path.isfile(state_file_path):
        logger.debug('found state file - will load it')
        
        with open(state_file_path) as f:
            try:
                climate_state = load(f)
            except:
                logger.error('cannot load state file.')
        
    else:
        logger.debug('no state file found. The climate controller will be set to off.')

def write_state_file(rel_path, update_interval: 'secs', force: bool):

    global climate_state

    if force or (time() >= climate_state['last_state_file_update_time'] + update_interval):

        # Go ahead and log the update time even though the file write is not done. This way
        # you won't bang on the file system over and over in the presence of errors.
        climate_state['last_state_file_update_time'] = time()
       
        try:
            #- state_file_path = getcwd() + rel_path
            state_file_path = path.join(state_directory_location, rel_path)
            logger.info('writing climate state file {}'.format(state_file_path))

            with open(state_file_path, 'w') as outfile:
                    dump(climate_state, outfile)
        except:
            logger.error('error encountered while writing state file: {}{}'.format(exc_info()[0], exc_info()[1]))


def make_help(prefix):

    def help():

        cmd_pre = "{}.".format(prefix)
        nul_pre = ' ' * len(cmd_pre)

        s =     cmd_pre + 'help()                     - Displays this help page.\n'
        s = s + cmd_pre + "cmd('start', day_index=n)  - Start a recipe on the designated day (0 based). If no day_index is\n"
        s = s + nul_pre + '                             supplied then start on day 0.\n'
        s = s + nul_pre + "                             e.g. {}.cmd('start', day_index=2) to start a recipe at 3rd day.\n".format(prefix)
        s = s + cmd_pre + "cmd('load_recipe'|'lr',\n" 
        s = s + nul_pre + '    recipe_path=path)      - Load a recipe file. If no recipe_file argument is given\n'
        s = s + nul_pre + '                             then load the default recipe file as specified in the configuration file.\n'
        s = s + nul_pre + "                           - e.g. {}.cmd('lr', recipe_path='/climate_recipes/test1.rcp')\n".format(prefix)
        s = s + cmd_pre + "cmd('stop')                - stop the current recipe.\n"
        s = s + cmd_pre + 'recipe()                   - Return the current recipe in JSON format.\n'
        s = s + cmd_pre + 'state()                    - Show climate controller state.\n'
        
        return s

    return help

def show_recipe():

    global climate_state

    if climate_state['recipe'] != None:
        #- return dumps(climate_state['recipe'])
        return dumps(climate_state['recipe'], indent=3)
    else:
        return None 

def show_date(date, prelude_msg):

    if date != None:
        return prelude_msg + ': {}\n'.format(datetime.datetime.fromtimestamp(date))
    else:
        return prelude_msg + ': None\n'


def show_state():

    global climate_state

    try:
        s =     'Mode:  {}\n'.format(climate_state['run_mode'])  

        if climate_state['recipe'] != None:
            s = s + 'Recipe id: {}\n'.format(climate_state['recipe']['id'])
        else:
            s = s + 'Recipe id: None\n'

        s = s + show_date(climate_state['recipe_start_time'], 'Recipe start time')

        s = s + 'Current day index: {}\n'.format(climate_state['cur_day'])
        s = s + 'Current hour: {}\n'.format(climate_state['cur_hour'])
        s = s + 'Current minute: {}\n'.format(climate_state['cur_min'])
        if climate_state['recipe'] != None and climate_state['cur_phase_index'] != None:
            s = s + 'Current phase: {}\n'.format(climate_state['recipe']['phases'][climate_state['cur_phase_index']]['name'])   

        s = s + 'Current phase index: {}\n'.format(climate_state['cur_phase_index'])   

        s = s + 'Grow light on: {}\n'.format(climate_state['grow_light_on'])
        s = s + show_date(climate_state['grow_light_last_on_time'], 'Last grow light on time')
        s = s + show_date(climate_state['grow_light_last_off_time'], 'Last grow light off time')

        s = s + 'Vent fan on: {}\n'.format(climate_state['vent_fan_on'])
        s = s + show_date(climate_state['vent_fan_last_on_time'], 'Last vent fan on time')
        s = s + show_date(climate_state['vent_fan_last_off_time'], 'Last vent fan off time')

        s = s + 'Circulation fan on: {}\n'.format(climate_state['circ_fan_on'])
        s = s + show_date(climate_state['circ_fan_last_on_time'], 'Last circulation fan on time')

        s = s + 'Air temperature: {}\n'.format(climate_state['cur_air_temp'])

        s = s + 'Air flush on: {}\n'.format(climate_state['air_flush_on'])
        s = s + show_date(climate_state['air_flush_last_on_time'], 'Last air flush on time')
        s = s + show_date(climate_state['air_flush_last_off_time'], 'Last air flush off time')

        s = s + 'Air heater on: {}\n'.format(climate_state['air_heater_on'])
        s = s + show_date(climate_state['air_heater_last_on_time'], 'Air heater last on time')
        s = s + show_date(climate_state['air_heater_last_off_time'], 'Air heater last off time')

        s = s + 'Air cooler on: {}\n'.format(climate_state['air_cooler_on'])
        s = s + show_date(climate_state['air_cooler_last_on_time'], 'Air cooler last on time')
        s = s + show_date(climate_state['air_cooler_last_off_time'], 'Air cooler last off time')

        s = s + 'Flood on: {}\n'.format(climate_state['flood_on'])
        s = s + show_date(climate_state['flood_last_on_time'], 'Last flood on time')
        s = s + show_date(climate_state['flood_last_off_time'], 'Last flood off time')

        s = s + 'Last state file write: {}\n'.format(datetime.datetime.fromtimestamp(
                                                     climate_state['last_state_file_update_time']).isoformat())
        return s

    except:
        logger.error('show_state command {}{}'.format(exc_info()[0], exc_info()[1]))
        return "Error - can't show state"

def make_cmd(config_args):

    def cmd(*args, **kwargs):

        global climate_state

        state_lock.acquire()

        try: 
            if len(args) == 1:
                if args[0] == 'start':

                    if 'day_index' in kwargs:
                        climate_state['cur_day'] = kwargs['day_index']
                    else:
                        climate_state['cur_day'] = 0

                    climate_state['run_mode'] = 'on'
                    climate_state['recipe_start_time'] = (datetime.datetime.now()\
                        - datetime.timedelta(days=climate_state['cur_day'])).timestamp()
                    return 'OK'
                elif args[0] == 'stop':
                    climate_state['run_mode'] = 'off'
                    climate_state['recipe_start_time'] = None
                    return 'OK'
                elif args[0] == 'load_recipe' or args[0] == 'lr':

                    if not 'recipe_path' in kwargs:
                        # TODO - Need to 1st check to make sure the file exists and then warn user if it does not exist.
                        res = load_recipe_file(config_args['default_recipe_file'])
                    else:
                        # Note that the recipe file will be looked for within the path specified by recipes_directory_location
                        # which is specified in the settings file.
                        res = load_recipe_file(path.join(kwargs['recipe_path']))

                    # write the climate state to disk
                    write_state_file(config_args['state_file'], 0, True)
                    
                    return res[1] 
                else:
                    return "illegal command: {}. please specify 'start' or 'stop'".format(args[0])
            else:
                return "you must supply a cmd (e.g. 'start')"
        except:
            logger.error('cmd execution failed: {}, {}'.format(exc_info()[0], exc_info()[1]))

        finally:
            state_lock.release()

    return cmd


def init_state(args):

    global climate_state

    # Initialize the climate controller state - this stuff will get replaced
    # if there is a state file to load
    climate_state['run_mode'] = 'off'
    climate_state['cur_phase_index'] = None
    climate_state['recipe_start_time'] = None

    # See if there is previous state in a state file  and load it if you have it, otherwise
    # create a state file so it's there the next time we reboot.
    load_state_file(args['state_file'])
    climate_state['last_state_file_update_time'] = time()

    # make sure the state has a recipe in case there is no state file.
    if 'recipe' not in climate_state or not climate_state['recipe']:
        load_recipe_file(args['default_recipe_file'])

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
    climate_state['vent_fan_last_on_time'] = None
    climate_state['vent_fan_last_off_time'] = None

    climate_state['circ_fan_on'] = False 
    climate_state['circ_fan_last_on_time'] = None

    climate_state['cur_air_temp'] = None

    climate_state['air_flush_on'] = False
    climate_state['air_flush_last_on_time'] = None
    climate_state['air_flush_last_off_time'] = None

    climate_state['air_cooler_on'] =  False
    climate_state['air_cooler_last_on_time'] = None
    climate_state['air_cooler_last_off_time'] = None

    climate_state['air_heater_on'] =  False
    climate_state['air_heater_last_on_time'] = None
    climate_state['air_heater_last_off_time'] = None

    climate_state['flood_on'] =  False
    climate_state['flood_last_on_time'] = None
    climate_state['flood_last_off_time'] = None

    climate_state['last_log_time'] = 0
    climate_state['log_cycle'] = False


# step_name -> e.g. light_intensity, air_fush
# value names -> tuple list of value names to return
#
def get_current_recipe_step_values(step_name, value_names, log_missing_entries=True):

    global climate_state

    values = None 

    try:
        
        times = climate_state['recipe']['phases'][climate_state['cur_phase_index']]['step'][step_name]

        if len(times) > 0:
            
            for t in times:

                past_start = False
                lte_end = False
               
                # accept times as either integers, floats (i.e the hour) or strings (e.g. hh:mm)
                if isinstance(t['start_time'], (int)):
                    start = [int(t['start_time']), 0]
                elif isinstance(t['start_time'], (float)):
                    start = [int(t['start_time']), int((t['start_time'] - int(t['start_time'])) * 60)]
                else:
                    start_time = datetime.datetime.strptime(t['start_time'], '%H:%M').time()
                    start = [start_time.hour, start_time.minute] 

                if start[0] <= climate_state['cur_hour']: 
                    #- if len(start) > 1:
                    if start[1] <= climate_state['cur_min']:
                        past_start = True
                    else:
                        past_start = False
                    #- else:
                        past_start = True 

                if isinstance(t['end_time'], (int)):
                    end = [int(t['end_time']), 59]
                elif isinstance(t['end_time'], (float)):
                    end = [int(t['end_time']), int((t['end_time'] - int(t['end_time'])) * 60)]
                else:
                    end_time = datetime.datetime.strptime(t['end_time'], '%H:%M').time()
                    end = [end_time.hour, end_time.minute] 
                
                #- if len(end) == 1:
                #-    if end[0] >= climate_state['cur_hour']: 
                #-        lte_end = True
                #-    else:
                #-        lte_end = False
                #- else:
                if (end[0] > climate_state['cur_hour']) or\
                   (end[0] == climate_state['cur_hour'] and end[1] >= climate_state['cur_min']):
                        lte_end = True
                else:
                    lte_end = False 
                
                # DEBUG logger.info('step name: {}, start: {}, end: {}, past_start: {}, lte_end: {}'.format(step_name, start, end, past_start, lte_end))
                #- if len(end) > 0:
                #-     logger.info('gte_start {}, lte_end {}'.format(past_start, lte_end))
                if past_start and lte_end:

                    values = {}

                    for vn in value_names:
                        if vn in t:
                            values[vn] = t[vn]
                        elif vn == "units":
                            # Unit's is an optional attribute, default it to minutes.
                            values["units"] = "minutes" 
                        #- else:
                        #-    logger.warning('cannot find value {} in step {}.'.format(vn, step_name))
                        else:
                            # An expected recipe value is missing. So do not return anything
                            if log_missing_entries:
                                log_entry_table.add_log_entry(logger.warning, 'cannot find value {} in step {}.'.format(vn, step_name)) 
                            return None

                    # You've found the step that cooresponds to the current time so now exit.
                    return values
            
            # If the code has gotten this far then there were no time intervals in the step that match the current time. 
            if log_missing_entries:
                log_entry_table.add_log_entry(logger.warning,
                    'There is no time interval for step {} for the time {}:{}'.format(step_name, climate_state['cur_hour'], climate_state['cur_min'])) 
            return None

        else:
            # There are no times defined in the recipe step 
            if log_missing_entries:
                log_entry_table.add_log_entry(logger.error, 'There are no recipe times for the  step named: {}.  Why?'.format(step_name)) 
            return None
            #- if climate_state['log_cycle']:
            #-     log_entry_table.add_log_entry(logger.error, 
            #-        'There are no recipe steps for: {}.  Why?'.format(step_name)) 

    except:
        log_entry_table.add_log_entry(logger.error, 
            'failed looking for step values: {}, {}, {}'.format(step_name, exc_info()[0], exc_info()[1]))

    return values

def check_lights(controller):

    global climate_state
  
    #TODO - units is an optional step value.  log_missing_entries won't log the non-presence of units. This is confusing. Is there
    #       a way to clean up the code to make optional step values more apparent.
    if get_current_recipe_step_values('light_intensity', ('interval', 'duration', 'units'), log_missing_entries = False):

        # There is a interval timer for the lights so use it.
        recipe_interval = run_interval_loop('light_intensity', climate_state['grow_light_on'], climate_state['grow_light_last_on_time']) 
        light_on = recipe_interval['turn_on'] 
    else:

        # There is no interval timer for the lights so look for a duration time in the recipe. 
        value = get_current_recipe_step_values('light_intensity', ('value',))

        # light_on = None
        light_on = False 

        if value != None:
            if 'value' in value.keys() and value['value']  == 1:
                #- if not climate_state['grow_light_on']: 
                light_on = True
            else:
                #- if climate_state['grow_light_on']:
                light_on = False 
        else:
            #- if climate_state['grow_light_on']:
            light_on = False 

    # Update the light controller to the current light on/off state
    #- if light_on != None:
    if light_on and not climate_state['grow_light_on']:
        climate_state['grow_light_on'] = True
        climate_state['grow_light_last_on_time'] = climate_state['cur_time'] 
        controller['cmd']('on', 'grow_light') 
    elif not light_on and climate_state['grow_light_on']:
        climate_state['grow_light_on'] = False 
        climate_state['grow_light_last_off_time'] = climate_state['cur_time']
        controller['cmd']('off', 'grow_light')


def run_interval_loop(loop_name, curr_on_state, last_on_time):

    global climate_state

    values = get_current_recipe_step_values(loop_name, ('interval', 'duration', 'units'))
    turn_on = None

    if values['units'] == 'seconds':
        duration = values['duration']
        interval = values['interval']
    else:
        duration = 60 * values['duration']
        interval = 60 * values['interval']

    if values != None and last_on_time != None:
        #- logger.info('curr_on_state {}, cur_time {}, last_on_time {}, duration {}, interval {}'.format(curr_on_state, climate_state['cur_time'],
        #-    last_on_time, values['duration'], values['interval']))
        if curr_on_state and\
           climate_state['cur_time'] - last_on_time > duration:
            turn_on = False
        elif not curr_on_state and\
             climate_state['cur_time'] - last_on_time > interval:
            turn_on = True
        else:
            # Waiting for next transition to on or off so leave the actuator in it's current state.
            turn_on = curr_on_state 
    elif values != None and last_on_time == None:
        # Assume this is a startup state.  There are recipe values for the actuator but 
        # no history so go ahead and start a cycle.
        turn_on = True
    else:
        # There are no recipe values for this actuator so don't turn it on.
        turn_on = False

    if turn_on == None:
        logger.error('{} recipe error. No action could be determined.'.format(loop_name))

    return {'turn_on':turn_on, 'interval':interval, 'duration':duration}


flood_sequence_state = {'cmd_index':None, 'cmd_start_time':None, 'cmd_duration':None, 'recipe_duration':None}

def reset_flood_sequence_state(cmd_index=None, clear_recipe_duration=True):

    global flood_sequence_state

    flood_sequence_state['cmd_index'] = cmd_index 
    flood_sequence_state['cmd_start_time'] = None
    flood_sequence_state['cmd_duration'] = None
    if clear_recipe_duration:
        flood_sequence_state['recipe_duration'] = None

def run_flood_loop(controllers, args):

    global flood_sequence_state

    log_entry_table.add_log_entry(logger.info, 'run_flood_loop called') 

    recipe_interval = run_interval_loop('flood', climate_state['flood_on'], climate_state['flood_last_on_time']) 
    on = recipe_interval['turn_on'] 

    # Turn flood on/off if necessary
    if on and not climate_state['flood_on']:
        logger.info('turning climate recipe flood on')
        climate_state['flood_on'] = True
        climate_state['flood_last_on_time'] = climate_state['cur_time']

        # Trigger the sequencer to run
        flood_sequence_state['cmd_index'] = 0
        flood_sequence_state['recipe_duration'] = recipe_interval['duration']
        
    if not on and climate_state['flood_on']:
        # Note: This controller supports multiple flood trays so it doesn't 
        #       necessarily stop flooding
        #       when the recipe interval duration has elapsed.  
        #       Rather the sequence logic below determines when the flooding is
        #       over.
        logger.info('turning climate recipe flood off - Note that sequence may continue on for multiple tray floods')
        climate_state['flood_on'] = False
        climate_state['flood_last_off_time'] = climate_state['cur_time']

    # Note: flood_sequence_state = {'cmd_index':None, 'cmd_start_time':None, 'cmd_duration':None}
   
    # The presence of a not None index triggers the sequencer to iterate 
    if flood_sequence_state['cmd_index'] or flood_sequence_state['cmd_index'] == 0 :
        # Run the sequence logic

        # The presence of a not None start time indicates a command is curretly waiting to time out.
        # Check for command timeout.
        if flood_sequence_state['cmd_start_time']:
            if (climate_state['cur_time'] - flood_sequence_state['cmd_start_time']) >= flood_sequence_state['cmd_duration']:
                # The command has timed out
                logger.info('sequence command duration has elapsed, command index: {}, command type: {}'.format(
                    flood_sequence_state['cmd_index'], args['sequence'][flood_sequence_state['cmd_index']]['cmd']))
                if flood_sequence_state['cmd_index'] >= len(args['sequence']) - 1:
                    #at end of command sequence
                    reset_flood_sequence_state()
                    logger.info('end of drain and flood sequence')
                    # No more commands in the sequence so return
                    return
                else:
                    reset_flood_sequence_state(cmd_index = flood_sequence_state['cmd_index'] + 1, 
                                               clear_recipe_duration=False)
                    # Move on and start the next command
            else:
                # waiting for the current command to time out so do nothing.
                return
        else:
            # Indicates the start of a sequence
            logger.info('starting a drain and flood sequence')

        # The command has not timed out so assume we are at the start of a command.
        cmd = args['sequence'][flood_sequence_state['cmd_index']]
        logger.info('starting sequence command: {}, command: {}'.format(
            flood_sequence_state['cmd_index'], cmd))

        # Set command start time and duration. All commands must have these two aspects.
        flood_sequence_state['cmd_start_time'] = climate_state['cur_time']
        if isinstance(cmd['duration'], (int, float)):
           flood_sequence_state['cmd_duration'] = cmd['duration']
        elif cmd['duration'] == 'recipe':
           #Note that recipe durations are in minutes. Sequence durations are in seconds.
           flood_sequence_state['cmd_duration'] = flood_sequence_state['recipe_duration'] * 60
        else:
            # unknown command duration  - abort the sequence
            log_entry_table.add_log_entry(logger.error, 'unknown command duration: {}'.format(cmd['duration'])) 
            # Reset the state so that the sequence won't start again till the climate recipe fires it.
            reset_flood_sequence_state()
            return

        # is it a hardware actuation?
        if cmd['cmd'] == 'hw_cmd':
            logger.info('issuing hardware command {} {}'.format(cmd['hw_id'], cmd['hw_cmd']))
            controllers[cmd['hw_int_index']]['cmd'](cmd['hw_cmd'], cmd['hw_id'])
        elif cmd['cmd'] == 'wait':
            logger.info('waiting....')

        else:
            # unknown command - abort the sequence
            log_entry_table.add_log_entry(logger.error, 'unknown sequence command: {}'.format(cmd['cmd'])) 
            # Reset the state so that the sequence won't start again till the climate recipe fires it.
            reset_flood_sequence_state()
   

def run_air_flush_loop(controller):

    global climate_state

    recipe_interval = run_interval_loop('air_flush', climate_state['air_flush_on'], climate_state['air_flush_last_on_time']) 
    flush_on = recipe_interval['turn_on'] 

    # Turn flush on/off if necessary
    if flush_on and not climate_state['air_flush_on']:
        logger.info('turning air flush on')
        climate_state['air_flush_on'] = True
        climate_state['air_flush_last_on_time'] = climate_state['cur_time']

    if not flush_on and climate_state['air_flush_on']:
        logger.info('turning air flush off')
        climate_state['air_flush_on'] = False
        climate_state['air_flush_last_off_time'] = climate_state['cur_time']

    return flush_on


def check_circ_fan(controller):

    global climate_state

    values = get_current_recipe_step_values('circ_fan', ('value',))

    if values != None and values['value'] == 1:
        #turn the circulation fan on
        if not climate_state['circ_fan_on']: 

            logger.info('turning circulation fan on') 
            climate_state['circ_fan_on'] = True
            climate_state['circ_fan_last_on_time'] = climate_state['cur_time']
            controller['cmd']('on', 'circ_fan') 
    else:
        if climate_state['circ_fan_on']: 
            logger.info('turning circulation fan off') 
            climate_state['circ_fan_on'] = False 
            climate_state['circ_fan_last_off_time'] = climate_state['cur_time']
            controller['cmd']('off', 'circ_fan') 

def run_heating_loop(controller, hysteresis):

    global climate_state

    values = get_current_recipe_step_values('air_temperature', ('low_limit', 'high_limit'))

    if values == None:
        # No recipe file settings for air temperature so turn the heater off if it is running, otherwise do nothing.
        logger.info('No air temperature recipe instructions found')
        if climate_state['air_heater_on']:
            logger.info('Turning the heater off.')
            climate_state['air_heater_last_off_time'] = climate_state['cur_time']
            controller['cmd']('off', 'air_heat')
        return

    # Don't heat unless the low limit is at least 1 C less than the high limit. This is to make sure the heater and
    # cooler don't fight each other.
    #
    if values ['high_limit'] - values['low_limit'] >= 1:

        if climate_state['cur_air_temp'] != None:
            if climate_state['cur_air_temp'] < values['low_limit'] - hysteresis:
                heater_on = True
            elif climate_state['cur_air_temp'] > values['low_limit']: 
                heater_on = False
            else:
                heater_on = climate_state['air_heater_on']
        else:
            logger.warning('No air temperature available. Will turn heater off.')
            heater_on = False 
    else:
        if climate_state['log_cycle']: 
            logger.error('Illegal values for high and low limits. High limit must be ' +\
                         'at least 1 degrees Celsius higher than low limit.')
        heater_on = False

    # Don't run the heater for more than 30 minutes.
    if climate_state['air_heater_on']:
        if climate_state['air_heater_last_on_time'] != None and\
            climate_state['cur_time'] - climate_state['air_heater_last_on_time'] > 30 * 60:

            heater_on = False

    # If the previous heater on period was greater than 29 minutes then leave the heater off for
    # 10 minutes
    if not climate_state['air_heater_on']:
        if (climate_state['air_heater_last_off_time'] != None and\
            climate_state['air_heater_last_on_time'] != None) and\
           (climate_state['air_heater_last_off_time'] - climate_state['air_heater_last_on_time']  > 29 * 60) and\
           (climate_state['cur_time'] - climate_state['air_heater_last_off_time']) < 10 * 60: 
           
            heater_on = False
            
    if heater_on == None:
        logger.error('air heating logic did not set a heater_on value')
        heater_on = False

    if heater_on and not climate_state['air_heater_on']:
        # Don't turn the heater on more than once per minute.
        if climate_state['air_heater_last_on_time'] == None or\
           climate_state['cur_time'] - climate_state['air_heater_last_on_time'] >= 60: 
               
            logger.info('turning the air heater on')
            climate_state['air_heater_on'] = True
            climate_state['air_heater_last_on_time'] = climate_state['cur_time']
            controller['cmd']('on', 'air_heat')

    if not heater_on and climate_state['air_heater_on']:
        logger.info('turning the air heater off')
        climate_state['air_heater_on'] = False 
        climate_state['air_heater_last_off_time'] = climate_state['cur_time']
        controller['cmd']('off', 'air_heat')

def run_cooling_loop(hw_int, hysteresis) -> bool:
    """ cooling controller that uses the vent fan """

    global climate_state

    values = get_current_recipe_step_values('air_temperature', ('low_limit', 'high_limit'))

    if values == None:
        # No air temperature settings in recipe file so turn the cooling off if it is running, otherwise do nothing.
        logger.info('No air temperature instructions found. Cooler wants vent fan off.')
        return False

    cooler_on = False

    # Don't cool unless the low limit is 1 C less than the high limit. This is to make sure the heater and
    # cooler don't fight each other.
    #
    if values['high_limit'] - values['low_limit'] >= 1:

        if climate_state['cur_air_temp'] != None:
            if climate_state['cur_air_temp'] >= values['high_limit'] + hysteresis:
                cooler_on = True
            elif climate_state['cur_air_temp'] < values['high_limit']:
                cooler_on = False
            else:
                cooler_on = climate_state['air_cooler_on'] 
        else:
            log_if_log_cycle(WARNING, 'air cooling loop: No air temperature avaialble. Will turn cooling off.') 
            #- logger.warning('air cooling loop: No air temperature avaialble. Will turn cooling off.')
            cooler_on  = False 
    else:
        if climate_state['log_cycle']: 
            logger.error('cooling loop: Illegal values for high and low limits. High limit must be ' +\
                         'at least 2 degrees Celsius higher than low limit.')
        cooler_on = False

    if cooler_on == None:
        logger.error('air cooling logic did not set a cooler_on value')
        cooler_on = False

    # Turn the cooler on/off if need be.
    if cooler_on and not climate_state['air_cooler_on']:
        logger.info('Turning the air cooler on.')
        climate_state['air_cooler_on'] = True
        climate_state['air_cooler_last_on_time'] = climate_state['cur_time']
    if not cooler_on and climate_state['air_cooler_on']:
        logger.info('Turning the air cooler off.')
        climate_state['air_cooler_on'] = False
        climate_state['air_cooler_last_off_time'] = climate_state['cur_time']

    return cooler_on 

def run_air_flush_and_cooling_loop(hw_int, hysteresis: int):

    global climate_state

    # Vent fan is shared for the purposes of honoring the climate recipe instructions for
    # air temperature and air flushes.
    cooling_on = run_cooling_loop(hw_int, hysteresis)
    flush_on = run_air_flush_loop(hw_int)

    if (cooling_on or flush_on) and not climate_state['vent_fan_on']:
        logger.info('turning vent fan on')
        climate_state['vent_fan_on'] = True
        climate_state['vent_fan_last_on_time'] = climate_state['cur_time']
        hw_int['cmd']('on', 'vent_fan')

    if (not cooling_on and not flush_on) and climate_state['vent_fan_on']:
        logger.info('turning vent fan off')
        climate_state['vent_fan_on'] = False
        climate_state['vent_fan_last_off_time'] = climate_state['cur_time']
        hw_int['cmd']('off', 'vent_fan')


def get_phase_index(cur_day_index, phases):

    try:

        rcp_day_index = 0

        for i in range(0, len(phases)):
            
            rcp_phase_cycles = phases[i]['cycles']

            if cur_day_index >= rcp_day_index and cur_day_index < rcp_day_index + rcp_phase_cycles: 

                return i

            else:
                rcp_day_index = rcp_day_index + rcp_phase_cycles

        #- logger.error('the current recipe does not apply to today. It may be over.')
        log_entry_table.add_log_entry(logger.error, 'the current recipe does not apply to today. It may be over.') 
        return None

    except:
        logger.error('cannot update phase index: {}, {}'.format(exc_info()[0], exc_info()[1]))
        return None


def log_if_log_cycle(level, msg): 

    global climate_state

    if climate_state['log_cycle']:
        logger.log(level, msg)

def update_climate_state(min_log_period, control_loops):

    global climate_state
    
    now = datetime.datetime.now()
    
    climate_state['cur_min'] = now.minute
    climate_state['cur_hour'] = now.hour
    
    if climate_state['recipe_start_time'] != None:
        climate_state['cur_day'] = (now - datetime.datetime.fromtimestamp(climate_state['recipe_start_time'])).days
    else:
        climate_state['cur_day'] = None

    climate_state['cur_phase_index'] = get_phase_index(climate_state['cur_day'], climate_state['recipe']['phases'])

    climate_state['cur_time'] = time()   # Return the time in seconds since the epoch as a floating point number.

    if climate_state['cur_time']  - climate_state['last_log_time'] >= min_log_period:   
        climate_state['last_log_time'] = climate_state['cur_time']
        climate_state['log_cycle'] =  True
    else:
        climate_state['log_cycle'] = False

    # Take an air temperature reading but only if one of the control functions needs the temperature.
    for c in control_loops:
        #- if c['need'] == 'air_temp' and c['enabled']:
        if c['need'] and c['enabled'] and 'air_temp' in c['need']:
            #- at = controller['get']('air_temp')
            at = c['args'][0]['get']('air_temp')
            try:
                climate_state['cur_air_temp'] = float(at['value'])
                break
            except:
                log_entry_table.add_log_entry(logger.warning, 
                    'cannot read air temperature. value returned by source is {} {} {}'.format(at, exc_info()[0], exc_info()[1]))


def create_control_loops(control_configs, app_state):

    controls = []
    
    for c in control_configs:

        if c['function'] == 'drain_and_flood':
            controls.append({'func':run_flood_loop, 'enabled':c['enabled'], 
                             'need':None, 'args':[[app_state[s] for s in c['hardware_interfaces']], c['args']]
                           })

        if c['function'] == 'circulation_fan':
            controls.append({'func':check_circ_fan, 'enabled':c['enabled'],
                             'need':None, 'args':[app_state[c['hardware_interface']]]})

        if c['function'] == 'grow_lights':
            controls.append({'func':check_lights, 'enabled':c['enabled'],
                             'need':None, 'args':[app_state[c['hardware_interface']]]})

        if c['function'] == 'air_heating':
            controls.append({'func':run_heating_loop, 'enabled':c['enabled'], 
                             'need':('air_temp',), 'args':[app_state[c['hardware_interface']], c['hysteresis']]})

        if c['function'] == 'air_cooling':
            controls.append({'func':run_air_flush_and_cooling_loop, 'enabled':c['enabled'], 
                             'need':('air_temp',), 'args':[app_state[c['hardware_interface']], c['hysteresis']]})

    return controls


def start(app_state, args, barrier):

    global climate_state

    logger.setLevel(args['log_level'])
    logger.info('starting climate controller thread')

    # Inject this resources commands into app_state
    app_state[args['name']] = {}
    app_state[args['name']]['cmd'] = make_cmd(args)
    app_state[args['name']]['help'] = make_help(args['name']) 
    app_state[args['name']]['recipe'] = show_recipe
    app_state[args['name']]['state'] = show_state

    # Load current state and recipe
    init_state(args)

    # Don't proceed until all the other resources are available.
    barrier.wait()    

    # by convention we expect a standard fopd hardware interface to exist.
    hw_int = app_state[args['hardware_interface']]

    # TODO - refactor to create the control loops before the barrier wait
    control_loops = create_control_loops(args['controls'], app_state) 


    while not app_state['stop']:

       state_lock.acquire()

       try:
           if climate_state['run_mode'] == 'on': 

               update_climate_state(args['min_log_period'], control_loops)
              
               for loop in control_loops:
                   if loop['enabled']:
                       loop['func'](*loop['args'])

           # Every once in a while write the state to the state file to make sure the file 
           # stays up to date.  
           # TODO: A more sophisticated system would write only when
           # changes were made.
           #
           write_state_file(args['state_file'], args['state_file_write_interval'], False)

       finally:
           state_lock.release()

       sleep(1)

    write_state_file(args['state_file'], args['state_file_write_interval'], True)
    logger.info('exiting climate controller thread')
