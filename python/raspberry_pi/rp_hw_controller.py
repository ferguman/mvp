# fopd resource
#
# This module implements hardware interfacing for a raspberry pi. It is system 
# agnostic being driven by a configuration file. It currently supports I2C and 
# digital output pins. One must write python classes for each I2C device and specify
# the class file name in the conig file.
#
from threading import Lock
from time import sleep
import re

import RPi.GPIO as GPIO

from python.logger import get_sub_logger 
logger = get_sub_logger(__name__)

def make_get(vals):

    def get(value_name):

        for v in vals:
            if v['value_name'] == value_name:
                return v

        return 'illegal value_name. Please specify one of {}.'.format(reading_names)

    return get

def make_sensor_list(args, vals):
    """ Create a sensor class for each i2c sensor in the i2c sensor list """

    sensors = []

    for s in args['i2c_bus']:

        # Instantiate and build all sensors.
        module = __import__('python.{}'.format(s['sensor_module']), fromlist=[s['sensor_name']])
        class_ = getattr(module, s['sensor_name'])
        sensors.append(class_(s, vals))

    return sensors

#
# Provide a lock so that multiple threads are forced to wait for commands that
# use the i2c bus. 
#
i2c_lock = Lock()

def update_i2c_sensor_readings(i2c_bus, sensors: list):
    """ ask each sensor to take readings and add them to vals """

    with i2c_lock:
        for s in sensors:
            s.update_sensor_readings()


def set_control_pins(controls, control_configs):
    """Set the Raspberry PI control pins as per the current command state """
    
    for c in controls:
        if control_configs['camera_pose'] and 'camera_pose' in c['config']:
            set_gpio_pin(c['config']['camera_pose'], c['config']['active_high'], c['config']['pin_num'])
        else:
            set_gpio_pin(c['state'], c['config']['active_high'], c['config']['pin_num'])


def set_gpio_pin(cmd, active_high: bool, pin_num: int):

    if (cmd == 'on' and active_high) or (cmd == 'off' and not active_high):
        GPIO.output(pin_num, 1)
    else:
        GPIO.output(pin_num, 0)


def make_controls(control_configs: list, controls: list):
    """ Make an array containing a dictionary for each control.  The dictionary
        contains the state (originally None), and configuration (a dictionary) for
        each control """

    pins_initialized = False
    #TODO - put in logic that checks that all config values are present and the values are ok 
    #       and that there are now bogus config settings.
    #TODO - currenlty we only accomadate digital_pins
    #- controls = []
    for c in control_configs:
        if c['type'].lower() == 'digital_pin':
            
            controls.append({'state':c['default'].lower(), 'config':c})

            if pins_initialized == False:
                GPIO.setwarnings(False)
                GPIO.setmode(GPIO.BOARD)
                pins_initialized = True
                
            GPIO.setup(c['pin_num'], GPIO.OUT)
            
            set_gpio_pin(controls[-1]['state'], controls[-1]['config']['active_high'], controls[-1]['config']['pin_num'])

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

def get(value_name):

    return 'OK'

def get_control(name: str, controls: list):

    for c in controls:
        if c['config']['name'].lower() ==  name.lower():
            return c

    return None

def make_cmd(controls: list, control_configs: dict):

    def cmd(*args): 

        cmd = args[0]

        # is this a show_target command
        if cmd == 'show_targets' or cmd == 'st':
            s  = None
            for c in controls:
                if s == None:
                    s = c['config']['name']
                else:
                    s = s + ', ' + c['config']['name']
            return s

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

        # is this an on or off command?
        elif cmd == 'camera_pose' or cmd == 'cp':

            if args[1] == 'on':
                control_configs['camera_pose'] = True 
                logger.info('posing for a picture')
                return 'OK'
            elif args[1] == 'off':
                control_configs['camera_pose'] = False
                logger.info('will stop posing for a picture')
                return 'OK'
            else:
                logger.error('Unknown pose command action {}'.format(args[1]))
                return 'Unknown pose command action {}'.format(args[1])

        logger.error('unknown command received: {}'.format(cmd))
        return "unknown cmd. Specify 'on' or 'off'"

    return cmd

# TBD - make a long and short form of this command. The long form would be used by local console
# for debuging. The short form would be used by MQTT to get the state of the arduiono.
# show_state('long' | 'short')
#
def make_show_state(overrides: dict, vals: list, controls: list):

    def show_state():

        s = 'Camera Pose is {}.\n'.format('on' if overrides['camera_pose'] else 'off')

        for v in vals:
            s = s + '{} = {} {}.\n'.format(v['value_name'], v['value'], v['units'])

        s = s + 'there are {} controls.\n'.format(len(controls))
        for c in controls:
            s = s + '{} is {}.\n'.format(c['config']['name'], c['state'])

        return s

    return show_state


def start(app_state, args, b):

    logger.info('Raspberry Pi hardware interface thread starting.')

    # These are variables hold the state of the controller: control configurations - currently
    # just camera pose, values - the current sensor readings, controls - the state and configuration
    # of each control point.
    control_configs = {'camera_pose':False}
    vals = []
    controls = []

    # Inject your commands into app_state.
    app_state[args['name']] = {} 
    app_state[args['name']]['help'] = make_help(args) 
    app_state[args['name']]['state'] = make_show_state(control_configs, vals, controls)
    app_state[args['name']]['sensor_readings'] = vals
    app_state[args['name']]['get'] = make_get(vals)
   
    # Initialize the sensors.
    # TODO: Currently this controller only supports i2c sensors but hopefully, one-wire, and other
    #       types of sensors can be added gracefully.
    if 'i2c_bus' in args:
        i2c_sensors = make_sensor_list(args, vals)

    # Initialize the control points
    # TODO: Currently only digital pin based control points are supported but hopefully other
    #       types can be added gracefully.
    if 'controls' in args:
        make_controls(args['controls'], controls)
    else:
        logger.error('There are no controls specified.')

    app_state[args['name']]['cmd'] = make_cmd(controls, control_configs)

    # Let the system know that you are good to go.
    b.wait()

    while not app_state['stop']:
     
        # Update fan and light switch digital control pins
        set_control_pins(controls, control_configs)

        # Read the i2c sensors
        update_i2c_sensor_readings(None, i2c_sensors) 

        sleep(1)

    logger.info('Raspberry Pi hardware interface thread stopping.')
