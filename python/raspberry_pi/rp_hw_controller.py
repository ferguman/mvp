# fopd resource
#
# This module implements hardware interfacing for a raspberry pi. It is system 
# agnostic being driven by a configuration file. It currently supports I2C and 
# digital output pins. One must write python classes for each I2C device and specify
# the class file name in the config file.
#
# This module uses the RPi.GPIO library.  There are other libraries such as
# https://gpiozero.readthedocs.io/en/stable/installing.html.
#
#
from threading import Lock
from time import sleep
import re

import RPi.GPIO as GPIO

from python.logger import get_sub_logger 
from python.LogFileEntryTable import LogFileEntryTable

logger = get_sub_logger(__name__)
log_entry_table = LogFileEntryTable(60*60)

def make_get(vals):

    def get(value_name):

        for v in vals:
            if v['value_name'] == value_name:
                return v

        return 'illegal value_name. Please specify one of {}.'.format(reading_names)

    return get


def make_sensor_list(args, sensor_readings):

    """ Create a sensor class for each i2c sensor listed in the i2c_bus list.
        Return a list containing all the classes.
        Note that each sensor class adds 0, 1, or more sensor reading values 
        to the sensor_readings array and these classes remember the indexes of their
        values so that they can update them with new sensor readings as
        they become available."""

    sensors = []

    if 'i2c_bus' in args:
        for s in args['i2c_bus']:

            # Instantiate and build all sensors.
            module = __import__('python.{}'.format(s['sensor_module']), fromlist=[s['sensor_name']])
            class_ = getattr(module, s['sensor_name'])
            #- sensors.append(class_(s, sensor_readings))
            sensors.append({'online':False, 'sensor':class_(s, sensor_readings)})

    return sensors

#
# Provide a lock so that multiple threads are forced to wait for commands that
# use the i2c bus. 
#
i2c_lock = Lock()

def update_i2c_sensor_readings(sensors: list):
    """ ask each sensor to take readings and add them to the
        sensor_readings array. Note the sensor_readings array is
        passed to each sensor class as they are created so that
        the classes can remember the location of it."""

    with i2c_lock:
        for s in sensors:
            #- s.update_sensor_readings()
            if s['online']:
                s['sensor'].update_sensor_readings()
            else:
                #- logger.error('sensor {} is off line'.format(s['sensor']))
                log_entry_table.add_log_entry(logger.error, 
                    'sensor {} is off line'.format(s['sensor'])) 


def update_control_outputs(controls, state):
    """Set the Raspberry PI control pins as per the current control state """
    
    for c in controls:
        if c['config']['type'] == 'digital_pin':
            if ('camera_pose' in state and state['camera_pose']) and\
               ('camera_pose' in c['config'] and c['config']['camera_pose'] == 'on'):
                set_gpio_pin('on', c['config']['active_high'], c['config']['pin_num'])
            else:
                set_gpio_pin(c['state'], c['config']['active_high'], c['config']['pin_num'])


def set_gpio_pin(cmd, active_high: bool, pin_num: int):

    if (cmd == 'on' and active_high) or (cmd == 'off' and not active_high):
        GPIO.output(pin_num, 1)
    else:
        GPIO.output(pin_num, 0)


def make_data_values(value_config_list: list, values: list):

    for c in value_config_list:
        if c['type'].lower() == 'digital_pin':
            
            values.append({'state':None, 'config':c})
                
            GPIO.setup(c['pin_num'], GPIO.IN)
            logger.info('Created digital pin {} input named {}'.format(c['pin_num'], c['name']))

        else:
            logger.error('Value type {} is not supported'.format(command_configs['type']))


def make_controls(control_configs: list, controls: list):

    #TODO - put in logic that checks that all config values are present and the values are ok 
    #       and that there are no bogus config settings.
    #TODO - currenlty we only accomadate digital_pins
    for c in control_configs:

        if c['type'].lower() == 'digital_pin':
            
            controls.append({'state':c['default'].lower(), 'config':c})
                
            GPIO.setup(c['pin_num'], GPIO.OUT)
            set_gpio_pin(controls[-1]['state'], controls[-1]['config']['active_high'], controls[-1]['config']['pin_num'])
            logger.info('Created digital pin {} output control named {}'.format(c['pin_num'], c['name']))

        elif c['type'].lower() == 'boolean':
            controls.append({'state':c['default'], 'config':c})
        else:
            logger.error('Control type {} is not supported'.format(c['type']))


def make_help(args):

    def help():

        prefix = args['name']

        s =     '{}.help()                            - Displays this help page.\n'.format(prefix)
        s = s + "{}.cmd('camera_pose' | 'cp', action) - if action = 'on' then Actuate the grow chamber lights for a picture,\n".format(prefix)
        s = s + "                                     - if action = 'off' then return the grow lights to the current state\n"
        s = s + "{}.cmd('on':'off', target)           - Turn an actuator on or off. Targets:\n".format(prefix)
        s = s + "                                       Run {}.cmd('st') to see the possible values for the target argument\n".format(prefix)
        s = s + "{}.cmd('show_targets'|'st')          - Show all the available target values\n".format(prefix)
        s = s + '{}.get(value_name)                   - Get value such as air temperature.\n'.format(prefix)
        s = s + '                                       The following value names are recognized:\n'
        s = s + '                                       humidity, air_temp, TBD add other available options to this help message.\n'
        s = s + '{}.state()                           - Show sensor readings and actuator state.\n'.format(prefix)
        s = s + "{}['sensor_readings']                - Return a dictionary containing all the current sensor readings.\n".format(prefix)
        s = s + '                                       Sensor readings are updated every second.'
        
        return s

    return help


def get_control(name: str, controls: list):

    for c in controls:
        if c['config']['name'].lower() ==  name.lower():
            return c

    return None

def make_cmd(controls: list, state: dict):

    def cmd(*args): 

        cmd = args[0]

        # is this a show_target command
        if cmd == 'show_targets' or cmd == 'st':
            # Show the controls as a comma seperated list on one line.
            s  = None
            for c in controls:
                if s == None:
                    s = c['config']['name']
                else:
                    s = s + ', ' + c['config']['name']
            return s

        # is it a true/false command
        elif isinstance(cmd, (bool,)):
            control = get_control(args[1], controls)

            if control:

                if cmd:
                    if not control['state']:
                        logger.info('Received {0} True command. Will set {0} to be True.'.format(control['config']['name']))
                elif not cmd:
                    if control['state']:
                        logger.info('Received {0} False command. Will set {0} to be False.'.format(control['config']['name']))

                control['state'] = cmd
                return 'OK'

            else:
                logger.error('Unknown on/off command action received: {}'.format(args[1]))
                return 'unknown target.'

        # is this an on or off command?
        elif cmd == 'on' or cmd == 'off':

            control = get_control(args[1], controls)

            if control:

                if cmd == 'on':
                    if control['state'] != 'on':
                        logger.info('Received {0} on command. Will turn {0} on.'.format(control['config']['name']))
                elif cmd == 'off':
                    if control['state'] != 'off':
                        logger.info('Received {0} off command. Will turn {0} off.'.format(control['config']['name']))

                control['state'] = cmd
                return 'OK'

            else:
                logger.error('Unknown on/off command action received: {}'.format(args[1]))
                return 'unknown target.'

        # is this a camera pose command. 
        elif cmd == 'camera_pose' or cmd == 'cp':

            if args[1] == 'on':
                #- control_state['camera_pose'] = True 
                state['camera_pose'] = True 
                logger.info('posing for a picture')
                return 'OK'
            elif args[1] == 'off':
                #- control_state['camera_pose'] = False
                state['camera_pose'] = False
                logger.info('will stop posing for a picture')
                return 'OK'
            else:
                logger.error('Unknown pose command action {}'.format(args[1]))
                return 'Unknown pose command action {}'.format(args[1])

        logger.error('unknown command received: {}'.format(cmd))
        return "unknown cmd. Specify 'on' or 'off'"

    return cmd

#- def make_show_state(overrides: dict, values: list, commands: list):
#- data_values and controls
def make_show_state(data_values: list, controls: list, state: dict):

    def show_state():

        s = 'Camera Pose is {}.\n'.format('on' if state['camera_pose'] else 'off')
        #- s = ''

        for v in data_values:
            s = s + '{} = {} ({}).\n'.format(v['value_name'], v['value'], v['units'])

        s = s + 'there are {} controls.\n'.format(len(controls))
        for c in controls:
            s = s + '{} is {}.\n'.format(c['config']['name'], c['state'])

        return s

    return show_state


def start(app_state, args, b):

    logger.setLevel(args['log_level'])
    logger.info('Raspberry Pi hardware interface thread starting.')

    # These are variables which hold the state of the controller: control configurations - currently
    # just camera pose, values - the current sensor readings, controls - the state and configuration
    # of each control point.
    # sensor_readings = []
    # vals = []
    state = {'camera_pose':False}
    controls = []
    data_values = []

    # Inject your commands into app_state.
    app_state[args['name']] = {} 
    app_state[args['name']]['help'] = make_help(args) 
    app_state[args['name']]['state'] = make_show_state(data_values, controls, state)
    app_state[args['name']]['sensor_readings'] = data_values
    app_state[args['name']]['get'] = make_get(data_values)
   
    # Initialize the i2c sensors.
    # TODO: Currently this controller only supports i2c sensors but hopefully, one-wire, and other
    #       types of sensors can be added gracefully.
    i2c_sensors = make_sensor_list(args, data_values)
    for s in i2c_sensors:
        s['online'] = s['sensor'].initialize()

    # Setup the GPIO based inputs and outputs
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)
    make_controls(args['controls'], controls)

    app_state[args['name']]['cmd'] = make_cmd(controls, state)

    # Let the system know that you are good to go.
    b.wait()

    while not app_state['stop']:
     
        # Update outputs 
        update_control_outputs(controls, state)

        # Read the i2c sensors
        update_i2c_sensor_readings(i2c_sensors) 

        sleep(1)

    #TODO - add code that sets each control to it's default value when the resource is shutting down.
    logger.info('Raspberry Pi hardware interface thread stopping.')
