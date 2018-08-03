from logging import getLogger
from time import sleep
import serial

"""
ser = serial.Serial('/dev/ttyACM0', 115200)
ser.write(b'(help)\n')
b = ser.read_until(b'OK')
print(b.decode('utf-8'))

"""

logger = getLogger('mvp.' + __name__)

def start(app_state, args):

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

    # check on the fc and see if it is ok
    # run unit tests and report failure in the log
    # if the unit tests fail then print a log message and exit the program!

    while not app_state['stop']:

        # Send the actuator command.
        # if success then 
        # Save the sensor readings
        # else log an error but don't flood the log.

        sleep(1)
