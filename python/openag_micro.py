from logging import getLogger 
from time import sleep, time
import re
import serial

"""
ser = serial.Serial('/dev/ttyACM0', 115200)
ser.write(b'(help)\n')
b = ser.read_until(b'OK')
print(b.decode('utf-8'))

"""

logger = getLogger('mvp.' + __name__)

p = re.compile(r'(\d+\.\d+)')

# FC1 Command Set -> humidifier, grow_light, ac_3, air_heat
cur_command = b'0,0,0,0,0\n'

# check on the fc and see if it is ok
# run unit tests and report failure in the log
# TBD:if the unit tests fail then print a log message and exit the program!
#
def initialize(args):

    logger.setLevel(args['log_level'])

    #- print('open ag micro starting...')
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

def extract_sensor_values(app_state, result):

    logger.debug('fc sensor values: {}'.format(result))

    # TBD: Maybe the thing to do is to pull the timestamp through from the arduiono
    #      if the time stamp does not move forward then detect this and blank out the
    #      sensor readings.
    ts = time()
    for r in app_state['sensor_readings']:
        r['ts'] = ts
    
    global p
    values = p.findall(result)

    if len(values) == 2:
        # Save each reading with a timestamp.
        # TBD: Think about converting to the "native" values (e.g. int, float, etc) here.
        app_state['sensor_readings'][0]['value'] = values[0]
        app_state['sensor_readings'][1]['value'] = values[1]
    else:
        logger.error('Error reading fc sensors. fc returned: {}'.format(result))
        for r in app_state['sensor_readings']:
            r['value'] = None

def grow_light_controller(cmd):

    logger.info('light controller command received: {}'.format(cmd))

    if cmd == 'on':
         cur_command = cur_command(inject 1 at nth postion)
    #     logger.info(light's on)
    # eif cmd = 'off':
    #     cur_command = inject 0 at nth position
    #     logger.info(light's off)
    # else
    #     logger.error(light error)

def start(app_state, args, b):

    logger.info('fc microcontroller interface thread starting.')

    #humidifier, grow_light, ac_3, air_heat
    # - cur_command = b'0,0,0,0,0\n'

    app_state['sensor_readings'] = [
            {'type':'environment', 'device_name':'arduino', 'device_id':args['device_id'],
             'subject':'air', 'subject_location_id':args['air_location_id'], 
             'attribute':'humidity', 'value':None, 'units':'Percentage', 'ts':None},
            {'type':'environment', 'device_name':'arduino', 'device_id':args['device_id'],
             'subject':'air', 'subject_location_id':args['air_location_id'], 
             'attribute':'temperature', 'value':None, 'units':'Celsius', 'ts':None}
            ]

    ser = initialize(args)

    # Send actuator command set to the Arduion and get back the sensor readings. 
    ser.write(cur_command)
    result = ser.read_until(b'\n').rstrip().decode('utf-8')
    extract_sensor_values(app_state, result)

    #Bring up your actuator interfaces
    app_state[args['name'] + '.grow_light'] = grow_light_controller

    # Let the system know that you are good to go.
    b.wait()

    while not app_state['stop']:

        # Send the actuator command.
        ser.write(cur_command)
        # if success then 
        result = ser.read_until(b'\n').rstrip().decode('utf-8')
        # Save the sensor readings
        extract_sensor_values(app_state, result)
        # else log an error but don't flood the log.

        sleep(1)

    logger.info('fc microcontroller interface thread stopping.')
