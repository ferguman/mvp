# fopd resource
#
# provides the following functions:
#    grow_light - on/off light controller named grow_light.
#    sensor_readings - A list of the fc sensor readings updated every 1 second.
#
from threading import Lock
from time import sleep, time
import re
import serial

from python.logger import get_sub_logger 

logger = get_sub_logger(__name__)

serial_interface_lock = Lock()

# FC1 Command Set -> humidifier, grow_light, ac_3, air_heat,
#                    vent fan, circulation fan, chamber lights, motherboard lights.
cur_command = [0,0,0,0,0,0,0,0]

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

# TBD - Think about putting this regular expression into the configuration file.
p = re.compile(r'(\d+\.\d+)|\d+')

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

    # TBD keep the next comment up to date.
    # 9 = the current 8 implemented sensors values ( of the fcv1 plus the status code.
    if len(values) == 9:
        # Save each reading with a timestamp.
        # TBD: Think about converting to the "native" values (e.g. int, float, etc) here.
        vals[0]['value'] = values[1] # snip the humidity 
        vals[1]['value'] = values[2] # snip the temperature
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
        return 'OK'
    elif cmd == 'off':
        cur_command[1] = 0
        logger.info('light off command received')
        return 'OK'
    else:
        logger.error('unknown command received: {}'.format(cmd))
        return "unknown light state specified. Specify 'on' or 'off'"

def make_help(args):

    def help():

        prefix = args['name']

        s =     '{}.help()                    - Displays this help page.\n'.format(prefix)
        s = s + "{}.grow_light('on'|'off')    - Turns the grow light on or off.\n".format(prefix)
        s = s + "{}['sensor_readings'][index] - Returns the sensor reading referenced by index.\n".format(prefix)
        s = s + "                               0: air humidity\n"
        s = s + "                               1: air temperature\n"
        s = s + "{0}.mc_cmd(mc_cmd_str)        - Micro-controller command.  Try {0}.uc_cmd('(help)') to get started.\n".format(prefix)
        s = s + "                               mc_cmd_str is specified as a string -> {0}.mc_cmd(\"(help)\") or {0}.mc_cmd('(help)')\n".format(prefix)
        s = s + "                               Embed quotes (\") by using the \ character -> {0}.mc_cmd(\"(c 'co2 'ser ".format(prefix) + r'\"Z\")")' + '\n'
        
        return s

    return help

def make_mc_cmd(ser):

    def mc_cmd(cmd_str):
        
        result = None

        # wait until the serial interface is free.
        serial_interface_lock.acquire()

        try:
            cmd_str_bytes = bytes(cmd_str, "ascii")
            ser.write(cmd_str_bytes + b'\n')
            result = ser.read_until(b'OK\r').rstrip().decode('utf-8')
            ser.reset_input_buffer()
        finally:
            serial_interface_lock.release()
            return result

    return mc_cmd

def log_result(c_old, c, result):

    if c_old != c:
        logger.info('Arduino command change old: {}'.format(c_old))
        logger.info('                       new: {}'.format(c))
        logger.info('Result of new command: {}'.format(result))


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
    # TBD - add code to acquire a lock on serial_interface_lock before the serial
    # line is used.
    ser.write(make_fc_cmd())
    result = ser.read_until(b'\n').rstrip().decode('utf-8')
    ser.reset_input_buffer()
    extract_sensor_values(result, vals)

    # Let the system know that you are good to go.
    b.wait()

    c = None
    c_old = None

    while not app_state['stop']:

        serial_interface_lock.acquire()

        try:
            # Send the actuator command.
            c_old = c
            c = make_fc_cmd()
            
            #- logger.debug('arduino command: {}'.format(c))
            ser.write(c)
            result = ser.read_until(b'\n').rstrip().decode('utf-8')
            ser.reset_input_buffer()

            log_result(c_old, c, result)

            #- logger.debug('arduino response: {}'.format(result))
            
            # Save the sensor readings
            extract_sensor_values(result, vals)
        finally:
            serial_interface_lock.release()

        sleep(1)

    logger.info('fc microcontroller interface thread stopping.')
