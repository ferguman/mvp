# fopd resource
#
# provides the following functions:
#    grow_light - on/off light controller named grow_light.
#    sensor_readings - A list of the fc sensor readings updated every 1 second.
#
from logging import getLogger 
from time import sleep, time
import re
import serial

logger = getLogger('mvp.' + __name__)

p = re.compile(r'(\d+\.\d+)')

# FC1 Command Set -> humidifier, grow_light, ac_3, air_heat
cur_command = [0,0,0,0]

# Create a binary string of the form: b'0,0,0,0\n'
def make_fc_cmd():

    global cur_command

    cmd = b'0'

    for b in cur_command:
        if b == 0:
            cmd = cmd + b',false'
        elif b == 1:
            cmd = cmd + b',true'
        else:
           logger.error('bad command bit: {}'.format(b))
           return b'0'

    return cmd + b'\n'

# check on the fc and see if it is ok
# run unit tests and report failure in the log
# TBD:if the unit tests fail then print a log message and exit the program!
#
def initialize(args):

    logger.setLevel(args['log_level'])

    logger.info('starting openag microcontroller monitor for food computer version 1')

    ser = serial.Serial(args['serial_port'], args['baud_rate'])

    # get the serial monitor intro.
    result = ser.read_until(b'\n').rstrip()
    logger.info('fc: {}'.format(result.decode('utf-8')))
    ser.reset_input_buffer()

    ser.write(b"(fc 'read)\n")
    result = ser.read_until(b'\n').rstrip()
    logger.info('fc: {}'.format(result.decode('utf-8')))
    ser.reset_input_buffer()

    #If the fc is off then turn it on. 
    if result[-4:] == b'OFF.':

        logger.info('turning fc on')
        ser.write(b"(fc 'on)\n")
        ser.read_until(b'OK')
        ser.reset_input_buffer()

        ser.write(b"(fc 'read)\n")
        result = ser.read_until(b'\n').rstrip()
        logger.info('fc: {}'.format(result.decode('utf-8')))
        ser.reset_input_buffer()

    return ser

def extract_sensor_values(result, vals):

    # logger.debug('fc sensor values: {}'.format(result))

    # TBD: Maybe the thing to do is to pull the timestamp through from the arduiono
    #      if the time stamp does not move forward then detect this and blank out the
    #      sensor readings.
    ts = time()
    #- for r in app_state['sensor_readings']:
    for r in vals:
        r['ts'] = ts
    
    global p
    values = p.findall(result)

    if len(values) == 3:
        # Save each reading with a timestamp.
        # TBD: Think about converting to the "native" values (e.g. int, float, etc) here.
        #- app_state['sensor_readings'][0]['value'] = values[0]
        #- app_state['sensor_readings'][0]['value'] = values[0]
        vals[0]['value'] = values[0]
        vals[1]['value'] = values[1]
    else:
        logger.error('Error reading fc sensors. fc returned: {}'.format(result))
        #- for r in app_state['sensor_readings']:
        for r in vals:
            r['value'] = None

def grow_light_controller(cmd):

    global cur_command

    if cmd == 'on':
        cur_command[1] = 1
        logger.info('light on command received')
    elif cmd == 'off':
        cur_command[1] = 0
        logger.info('light off command received')
    else:
        logger.error('unknown command received: {}'.format(cmd))

def make_help(args):

    def help():

        prefix = args['name']

        s =     '{}.help()                    - Displays this help page.\n'.format(prefix)
        s = s + "{}.grow_light('on'|'off')    - Turns the grow light on or off.\n".format(prefix)
        s = s + "{}['sensor_readings'][index] - Returns the sensor reading referenced by index.\n".format(prefix)
        s = s + "                               0: air humidity\n"
        s = s + "                               1: air temperature\n"
        s = s + "{0}.mc_cmd(uc_cmd_str)        - Micro-controller command.  Try {0}.uc_cmd('(help)') to get started.\n".format(prefix)
        
        return s

    return help

# TBD- Need to create some sort of locking mechanism around the ser object so that user
#      intiated commands don't conflict with commands sent in the while loop.
#      Also need to turn the user entered value in a byte string.
def make_mc_cmd(ser):

    def mc_cmd(cmd_str):
        
        ser.write(cmd_str + b'\n')
        result = ser.read_until(b'OK\r').rstrip().decode('utf-8')
        return result

    return mc_cmd

def start(app_state, args, b):

    logger.info('fc microcontroller interface thread starting.')

    ser = initialize(args)

    # Inject your commands into app_state.
    app_state[args['name']] = {} 
    app_state[args['name']]['help'] = make_help(args) 
    app_state[args['name']]['grow_light'] = grow_light_controller
    app_state[args['name']]['mc_cmd'] = make_mc_cmd(ser)
    
    app_state[args['name']]['sensor_readings'] = [
               {'type':'environment', 'device_name':'arduino', 'device_id':args['device_id'],
                'subject':'air', 'subject_location_id':args['air_location_id'], 
                'attribute':'humidity', 'value':None, 'units':'Percentage', 'ts':None},
               {'type':'environment', 'device_name':'arduino', 'device_id':args['device_id'],
                'subject':'air', 'subject_location_id':args['air_location_id'], 
                'attribute':'temperature', 'value':None, 'units':'Celsius', 'ts':None}
    ]
    vals = app_state[args['name']]['sensor_readings']


    # Send actuator command set to the Arduino and get back the sensor readings. 
    ser.write(make_fc_cmd())
    result = ser.read_until(b'\n').rstrip().decode('utf-8')
    ser.reset_input_buffer()
    extract_sensor_values(result, vals)

    # Let the system know that you are good to go.
    b.wait()

    while not app_state['stop']:

        # Send the actuator command.
        c = make_fc_cmd()
        # logger.debug('fc cmd: {}'.format(c))
        ser.write(make_fc_cmd())
        result = ser.read_until(b'\n').rstrip().decode('utf-8')
        ser.reset_input_buffer()
        
        # Save the sensor readings
        extract_sensor_values(result, vals)

        sleep(1)

    logger.info('fc microcontroller interface thread stopping.')
