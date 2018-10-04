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

reading_names = {'humidity':0, 'air_temp':1, 'light_lum':2, 'light_par':3, 'air_co2':4, 'ph':5, 'water_temp':6, 
                 'water_ec':7, 'shell_off':8, 'window_off':9}

def make_get(vals):

    def get(value_name):
        if value_name in reading_names:
            return vals[reading_names[value_name]] #vals[reading_names[value_name]]
        else:
            return 'illegal value_name. Please specify one of {}.'.format(reading_names)

    return get

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

# Provide a lock so that multiple threads are forced to wait for commands that
# use the Arudiuno serial interface
#
serial_interface_lock = Lock()

# FC1 Command Set -> humidifier, grow_light, ac_3, air_heat,
#                    vent fan, circulation fan, chamber lights, motherboard lights.
#
target_indexes = {'humidifier':0, 'grow_light':1, 'ac 3 switch':2,'air_heat':3, 
                  'vent_fan':4, 'circ_fan':5, 'chamber_lights':6, 'mb_lights':7}
#
cur_command = [0,0,0,0,0,0,0,0]
cur_mc_cmd_str = None
old_mc_cmd_str = None
cur_mc_response = None
old_mc_response = None

# Create a command string for the Arduino -> b'0,false,true,...false\n'
def make_fc_cmd(mc_state):

    # first build an array that holds all the arduino commands 
    cmds = []

    # scan the cur_command bits
    for v in cur_command:
        if v == 0:
            cmds.append(False)
        elif v == 1:
            cmds.append(True)
        else:
           logger.error('bad command value: {}'.format(b))
           # dump and run. this is bad!
           return b'0'
    
    # if the system is in camera pose mode then override the light commands
    # in order to give good lighting for the camera.
    if mc_state['camera_pose']:
        cmds[target_indexes['grow_light']] = False
        cmds[target_indexes['chamber_lights']] = True

    # walk the command array and build the arduino command
    #
    cmd = b'0'
    
    for b in cmds:
        if b == False:
            cmd = cmd + b',false'
        elif b == True:
            cmd = cmd + b',true'
        else:
           logger.error('bad command boolean: {}'.format(b))
           # dump and run. this is bad!
           return b'0'

    return cmd + b'\n'

    """
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
    """


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

"""
reading_names = {'humidity':0, 'air_temp':1, 'light_lum':2, 'light_par':3, 'air_co2':4, 'ph':5, 'water_temp':6, 
                 'water_ec':7, 'shell_off':8, 'window_off':9}
target_indexes = {'humidifier':0, 'grow_light':1, 'ac 3 switch':2,'air_heat':3, 
                  'vent_fan':4, 'circ_fan':5, 'chamber_lights':6, 'mb_lights':7}
"""

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
        s = s + "{0}.mc_cmd(mc_cmd_str)               - Micro-controller command.  Try {0}.uc_cmd('(help)') to get started.\n".format(prefix)
        s = s + "                                       mc_cmd_str is specified as a string -> {0}.mc_cmd(\"(help)\") or {0}.mc_cmd('(help)')\n".format(prefix)
        s = s + "                                       Embed quotes (\") by using the \ character -> {0}.mc_cmd(\"(c 'co2 'ser ".format(prefix) + r'\"Z\")")' + '\n'
        s = s + '{}.state()                           - Show sensor readings and actuator state.\n'.format(prefix)
        s = s + "{}['sensor_readings'][index]         - Returns the sensor reading referenced by index.\n".format(prefix)
        s = s + "                                       0: air humidity\n"
        s = s + "                                       1: air temperature\n"
        
        return s

    return help

def get(value_name):

    return 'OK'

def make_cmd(mc_state, ser):

    def cmd(*args): 

        cmd= args[0]

        # is this a show_target command
        if cmd == 'show_targets' or cmd == 'st':
            s  = None
            for t in target_indexes:
                if s == None:
                    s = t
                else:
                    s = s + ', ' + t
            return s

        # is this an on or off command?
        elif cmd == 'on' or cmd == 'off':

            target = args[1]

            if target in target_indexes:

                target_index = target_indexes[target]
                global cur_command

                if cmd == 'on':
                    if cur_command[target_index] == 0:
                        logger.info('Recevied {0} on command. Will turn {0} on.'.format(target))
                    cur_command[target_index] = 1
                    return 'OK'
                elif cmd == 'off':
                    if cur_command[target_index] == 1:
                        logger.info('Recevied {0} off command. Will turn {0} off.'.format(target))
                    cur_command[target_index] = 0
                    return 'OK'
            else:
                logger.error('Unknown on/off command action received: {}'.format(target))
                return 'unknown target.'

        # is this an on or off command?
        elif cmd == 'camera_pose' or cmd == 'cp':

            if args[1] == 'on':
                mc_state['camera_pose'] = True 

                # send a command to the arduino now so the lights go into pose mode ASAP
                send_mc_cmd(ser, make_fc_cmd(mc_state))

                logger.info('posing for a picture')
                return 'OK'
            elif args[1] == 'off':
                mc_state['camera_pose'] = None
                logger.info('will stop posing for a picture')
                return 'OK'
            else:
                logger.error('Unknown pose command action {}'.format(args[1]))
                return 'Unknown pose command action {}'.format(args[1])

        logger.error('unknown command received: {}'.format(cmd))
        return "unknown cmd. Specify 'on' or 'off'"

    return cmd

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
def send_mc_cmd(ser, cmd_str):

    """
    # Update current state - So logger routines can intelligently log changes
    global old_mc_cmd_str, cur_mc_cmd_str, old_mc_response, cur_mc_response
    old_mc_cmd_str = cur_mc_cmd_str
    cur_mc_cmd_str = make_fc_cmd(mc_state)
    old_mc_response = cur_mc_response
    
    # Send the current command to the fc.
    cur_mc_response = send_mc_cmd(ser, cur_mc_cmd_str)
    """

    serial_interface_lock.acquire()

    try:
        # Update current state - So logger routines can intelligently log changes
        global old_mc_cmd_str, cur_mc_cmd_str, old_mc_response, cur_mc_response
        old_mc_cmd_str = cur_mc_cmd_str
        cur_mc_cmd_str = cmd_str 
        old_mc_response = cur_mc_response
    
        ser.write(cmd_str)
        mc_response = ser.read_until(b'OK\r\n')
        ser.reset_input_buffer()
    finally:
        serial_interface_lock.release()

    cur_mc_response = tokenize_mc_response(mc_response)
    log_cmd_changes()
    
    return cur_mc_response 


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

def initialize_fc(mc_state, ser, vals, iterations):

    # Turn the food computer micro-controller loop on
    logger.info("asking the food computer if it is on.")
    log_mc_response(send_mc_cmd(ser, b"(fc 'read)\n"))
    logger.info("regardless of response tell fc to turn on.")
    send_mc_cmd(ser, b"(fc 'on)\n")
    log_mc_response(send_mc_cmd(ser, b"(fc 'read)\n"))
   
    # Ping the mc twice so that it does two update loops
    for i in range(0, iterations):
       log_mc_response(send_mc_cmd(ser, make_fc_cmd(mc_state)))
       sleep(1)


def start(app_state, args, b):

    logger.info('fc microcontroller interface thread starting.')

    # Start a serial connection with the Aruduino - Note that this resets the Arduino.
    ser = start_serial_connection(args)

    # We have one state variable so no need of a state structure
    mc_state = {}
    mc_state['camera_pose'] = None

    # Inject your commands into app_state.
    app_state[args['name']] = {} 
    app_state[args['name']]['help'] = make_help(args) 
    app_state[args['name']]['cmd'] = make_cmd(mc_state, ser)
    app_state[args['name']]['mc_cmd'] = make_mc_cmd(ser)
    app_state[args['name']]['state'] = show_state
   
    vals = app_state[args['name']]['sensor_readings'] = create_sensor_reading_dict(args)
    app_state[args['name']]['get'] = make_get(vals)

    # Start the fc loop and and let it run for n seconds where n = args['mc_start_delay'].
    # 10 is recommened for the fc version 1 in order to wait for the
    # co2 reading to be accurate.  TBD: There are more sophisticated ways - such as making the co2
    # reading "unavailible" until it is available.
    initialize_fc(mc_state, ser, vals, args['mc_start_delay'])

    # Take the first set of sensor readings
    extract_sensor_values(send_mc_cmd(ser, make_fc_cmd(mc_state)), vals)

    # Let the system know that you are good to go.
    b.wait()

    while not app_state['stop']:
      
        """-
        # Update current state - So logger routines can intelligently log changes
        global old_mc_cmd_str, cur_mc_cmd_str, old_mc_response, cur_mc_response
        old_mc_cmd_str = cur_mc_cmd_str
        cur_mc_cmd_str = make_fc_cmd(mc_state)
        old_mc_response = cur_mc_response
        
        # Send the current command to the fc.
        cur_mc_response = send_mc_cmd(ser, cur_mc_cmd_str)
        """

        # Send a command string to the Arduino that actuates as per the current controller state.
        cur_mc_response = send_mc_cmd(ser, make_fc_cmd(mc_state))

        # Look for a set of sensor readings and extract them if you find one.
        extract_sensor_values(cur_mc_response, vals)

        # Look for warnings and errors.
        #- log_cmd_changes()

        sleep(1)

    logger.info('fc microcontroller interface thread stopping.')
