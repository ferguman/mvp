# fopd resource
#
# TBD - review and finish the following comments
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

# The Food Computer V1 senses 8 things with 6 sensors -> air humidity, air temp, light par, light lumens,
# air co2, water ph, water temp, and water ec.
# TBD Need to add window and shell switch sensors.
def create_sensor_reading_dict(args):

   return [
               {'type':'environment', 'device_name':'arduino', 'device_id':args['device_id'],
                'subject':'air', 'subject_location_id':args['air_location_id'], 
                'attribute':'humidity', 'value':None, 'units':'Percentage', 'ts':None},
               {'type':'environment', 'device_name':'arduino', 'device_id':args['device_id'],
                'subject':'air', 'subject_location_id':args['air_location_id'], 
                'attribute':'temperature', 'value':None, 'units':'Celsius', 'ts':None},
               {'type':'environment', 'device_name':'arduino', 'device_id':args['device_id'],
                'subject':'light', 'subject_location_id':args['grow_light_location_id'], 
                'attribute':'lum', 'value':None, 'units':'lm', 'ts':None},
               {'type':'environment', 'device_name':'arduino', 'device_id':args['device_id'],
                'subject':'light', 'subject_location_id':args['grow_light_location_id'], 
                'attribute':'par', 'value':None, 'units':'mol/sec', 'ts':None},
               {'type':'environment', 'device_name':'arduino', 'device_id':args['device_id'],
                'subject':'air', 'subject_location_id':args['air_location_id'], 
                'attribute':'co2', 'value':None, 'units':'ppm', 'ts':None},
               {'type':'environment', 'device_name':'arduino', 'device_id':args['device_id'],
                'subject':'water', 'subject_location_id':args['water_location_id'], 
                'attribute':'ph', 'value':None, 'units':'None', 'ts':None},
               {'type':'environment', 'device_name':'arduino', 'device_id':args['device_id'],
                'subject':'water', 'subject_location_id':args['water_location_id'], 
                'attribute':'temperature', 'value':None, 'units':'Celsius', 'ts':None},
               {'type':'environment', 'device_name':'arduino', 'device_id':args['device_id'],
                'subject':'water', 'subject_location_id':args['water_location_id'], 
                'attribute':'ec', 'value':None, 'units':'mS/cm', 'ts':None},
               {'type':'environment', 'device_name':'arduino', 'device_id':args['device_id'],
                'subject':'air', 'subject_location_id':args['air_location_id'], 
                'attribute':'shell_off', 'value':None, 'units':'None', 'ts':None},
               {'type':'environment', 'device_name':'arduino', 'device_id':args['device_id'],
                'subject':'air', 'subject_location_id':args['air_location_id'], 
                'attribute':'window_off', 'value':None, 'units':'None', 'ts':None},
   ]

# Provide a lock so that multiple threads can share the serial interface to the Arduino
serial_interface_lock = Lock()

# FC1 Command Set -> humidifier, grow_light, ac_3, air_heat,
#                    vent fan, circulation fan, chamber lights, motherboard lights.
cur_command = [0,0,0,0,0,0,0,0]
cur_mc_cmd_str = None
old_mc_cmd_str = None
cur_mc_response = None
old_mc_response = None

# Create a binary string of the form: b'0,1, .... \n'
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


def extract_sensor_values(mc_response, vals):

    # Note these globals -> global old_mc_cmd_str, cur_mc_cmd_str, old_mc_response, cur_mc_response

    # TBD: Maybe the thing to do is to pull the timestamp through from the arduiono
    #      if the time stamp does not move forward then detect this and blank out the
    #      sensor readings.
    ts = time()
    for r in vals:
        r['ts'] = ts
   
    readings_found = False

    for msg in mc_response:
        if msg[0:1] == '0':
            values = re.compile(r'(\d+\.\d+)|\d+').findall(msg)

            # TBD keep the next comment up to date.
            # 11 = the current 10 implemented sensors values of the fcv1 plus the status code.
            if len(values) == 11:
                readings_found = True
                # Save each reading with a timestamp.
                # TBD: Think about converting to the "native" values (e.g. int, float, etc) here.
                for i in range (1, 11):
                   vals[i-1]['value'] = values[i] 

    if not readings_found:
        logger.error('Error reading fc sensors. fc returned: {}'.format(result))
        for r in vals:
            r['value'] = None

def make_help(args):

    def help():

        prefix = args['name']

        s =     '{}.help()                    - Displays this help page.\n'.format(prefix)
        s = s + "{}.grow_light('on'|'off')    - Turns the grow light on or off.\n".format(prefix)
        s = s + "{0}.mc_cmd(mc_cmd_str)        - Micro-controller command.  Try {0}.uc_cmd('(help)') to get started.\n".format(prefix)
        s = s + "                               mc_cmd_str is specified as a string -> {0}.mc_cmd(\"(help)\") or {0}.mc_cmd('(help)')\n".format(prefix)
        s = s + "                               Embed quotes (\") by using the \ character -> {0}.mc_cmd(\"(c 'co2 'ser ".format(prefix) + r'\"Z\")")' + '\n'
        s = s + '{}.state()                   - Show sensor readings and actuator state.\n'.format(prefix)
        s = s + "{}['sensor_readings'][index] - Returns the sensor reading referenced by index.\n".format(prefix)
        s = s + "                               0: air humidity\n"
        s = s + "                               1: air temperature\n"
        
        return s

    return help

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


def make_mc_cmd(ser):

    def mc_cmd(cmd_str):
        
        result = None

        # wait until the serial interface is free.
        serial_interface_lock.acquire()

        try:
            cmd_str_bytes = bytes(cmd_str, "ascii")
            ser.write(cmd_str_bytes + b'\n')
            result = ser.read_until(b'OK\r\n').rstrip().decode('utf-8')
            ser.reset_input_buffer()
        finally:
            serial_interface_lock.release()
            return result

    return mc_cmd

def cur_mc_response_as_str():

    # Note the use of the global cur_mc_response
    if cur_mc_response == None:
        return 'None'
    else:
        return '\n'.join(cur_mc_response)

# TBD - make a long and short form of this command. The long form would be used by local console
# for debuging. The short form would be used by MQTT to get the state of the arduiono.
# show_state('long' | 'short')
#
def show_state():

    # Note use of global cur_mc_cmd_str
    return 'current micro-controller string: {}\n'.format(cur_mc_cmd_str) +\
           'current micro-controller response: {}\n'.format(cur_mc_response_as_str())


def log_mc_response(response):

    for msg in response:

        if msg[0:1] == '0':
            logger.info('sensor readings: {}'.format(msg))
        elif msg[0:1] == '1':
            logger.warning('micro warning: {}'.format(msg))
        elif msg[0:1] == '2':
            logger.error('micro error: {}'.format(msg))
        elif msg[0:30] == 'OpenAg Serial Monitor Starting':
            logger.info('micro reset detected: {}'.format(msg))
        else:
            logger.info('micro response: {}'.format(msg))

def log_cmd_changes():

    # Note use of globals cur_mc_cmd_str, old_mc_cmd_str, and cur_mc_response

    show_response = False

    if cur_mc_cmd_str != old_mc_cmd_str:
        
        logger.info('Arduino command change old: {}'.format(old_mc_cmd_str))
        logger.info('                       new: {}'.format(cur_mc_cmd_str))
        show_response = True

    if (old_mc_response == None) or (len(cur_mc_response) != len(old_mc_response)):

        logger.info('Arduino response (i.e. # of lines) changed')
        show_response = True

    if show_response:
        log_mc_response(cur_mc_response)

def tokenize_mc_response(mc_response):

    # Remove the trailing "\r\nOK" and then split the micro-controller's response into an array of lines.
    return mc_response.decode('utf-8')[0:-6].split('\r\n')


# The micro-controller responds to food computer commands as follows:
# If any module (a sensor or an actuator) has a warning or failure then a message line is returned 
# for each such failing module. The format of these message lines
# is "status level, module name, status code, status message".
# If any sensor has a warning or failure then no sensor readings are returned.  If sensor
# readings are returned then they are sent on a line formatted as:
# "0,x1,x2, ... xn" where xn is either an integer (e.g. 20) or a float (e.g. 20.5).
# Lastly the string "OK\r\n" is returned to mark the end of the micro-controller's response
# to the command.
#
def send_mc_cmd(ser, c):

    serial_interface_lock.acquire()
    try:
        ser.write(c)
        mc_response = ser.read_until(b'OK\r\n')
        ser.reset_input_buffer()
    finally:
        serial_interface_lock.release()

    return tokenize_mc_response(mc_response)


# TBD: check on the fc and see if it is ok
# run unit tests and report failure in the log
# TBD:if the unit tests fail then print a log message and exit the program!
#
def start_serial_connection(args):

    logger.setLevel(args['log_level'])

    logger.info('starting openag microcontroller monitor for food computer version 1')

    # Starting the serial port resets the Arduino. 
    ser = serial.Serial(args['serial_port'], args['baud_rate'])

    # The Arduino should respond with the serial  monitor salutation (i.e. 
    # "OpenAg Serial Monitor Starting" and any warnings or errors generated by the modules during
    # the invokation of their begin methods.
    # TBD - Add checking for failed startup messages.
    log_mc_response(tokenize_mc_response(ser.read_until(b'OK\r\n')))
    ser.reset_input_buffer()

    return ser

def initialize_fc(ser, vals, iterations):

    # Turn the food computer micro-controller loop on
    logger.info("asking the food computer if it is on.")
    log_mc_response(send_mc_cmd(ser, b"(fc 'read)\n"))
    logger.info("regardless of response tell fc to turn on.")
    send_mc_cmd(ser, b"(fc 'on)\n")
    log_mc_response(send_mc_cmd(ser, b"(fc 'read)\n"))
   
    # Ping the mc twice so that it does two update loops
    for i in range(0, iterations):
       log_mc_response(send_mc_cmd(ser, make_fc_cmd()))
       sleep(1)


def start(app_state, args, b):

    logger.info('fc microcontroller interface thread starting.')

    # Start a serial connection with the Aruduino - Note that this resets the Arduino.
    ser = start_serial_connection(args)

    # Inject your commands into app_state.
    app_state[args['name']] = {} 
    app_state[args['name']]['help'] = make_help(args) 
    app_state[args['name']]['grow_light'] = grow_light_controller
    app_state[args['name']]['mc_cmd'] = make_mc_cmd(ser)
    app_state[args['name']]['state'] = show_state
   
    vals = app_state[args['name']]['sensor_readings'] = create_sensor_reading_dict(args)

    # Start the fc loop and and let it run for n seconds where n = args['mc_start_delay'].
    # 10 is recommened for the fc version 1 in order to wait for the
    # co2 reading to be accurate.  TBD: There more sophisticated ways - such as making the co2
    # reading "unavailible" until it is available.
    initialize_fc(ser, vals, args['mc_start_delay'])

    # Take the first set of sensor readings
    extract_sensor_values(send_mc_cmd(ser, make_fc_cmd()), vals)

    # Let the system know that you are good to go.
    b.wait()

    while not app_state['stop']:
       
        # Update current state - So logger routines can intelligently log changes
        global old_mc_cmd_str, cur_mc_cmd_str, old_mc_response, cur_mc_response
        old_mc_cmd_str = cur_mc_cmd_str
        cur_mc_cmd_str = make_fc_cmd()
        old_mc_response = cur_mc_response
        
        # Send the current command to the fc.
        cur_mc_response = send_mc_cmd(ser, cur_mc_cmd_str)

        # Look for a set of sensor readings and extract them if you find one.
        extract_sensor_values(cur_mc_response, vals)

        # Look for warnings and errors.
        log_cmd_changes()

        sleep(1)

    logger.info('fc microcontroller interface thread stopping.')
