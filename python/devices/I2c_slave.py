import threading
import smbus2

from sys import exc_info
from time import sleep, time

from python.logger import get_sub_logger 

#- address = 0x40
#- rh_no_hold = 0xf5
#-previous_temp = 0xe0

#TODO need to figure out logging
logger = get_sub_logger(__name__)

class I2c_slave():
    """ Parent class for raspberry pi controller i2c slave devices.
        Provides the following functions to slaves:
        1) Inserts configured observations into the system supplied list of
           system observations.
    """

    def __init__(self, config: dict, vals: list):

        #TODO: Investigate making the bus a static instance in the application. 
        self.bus = smbus2.SMBus(1)

        self.config = config

        if 'i2c_address' in config:
            self.i2c_addr = config['i2c_address']
        else:
            self.i2c_addr = None

        self.init_sensor_value_list(vals)

    def init_sensor_value_list(self, vals: list):

       """ vals is the master list of sensor readings.  It may contain readings 
           from sensors other than this one.  Tack this sensor's readings onto the list
           and remember where in the list the readings are at. """
      
       self.vals = vals
       
       self.attribute_value_indexes = {}

       for a in self.config['attributes']:

           self.vals.append(
               {'value_name':a['value_name'], 'type':'environment', 'device_name':self.config['device_name'], 
                'device_id':self.config['device_id'],
                'subject':a['subject'], 'subject_location_id':a['subject_location_id'], 
                'attribute':a['attribute'], 'value':None, 'units':a['units'], 'ts':None})

           #- self.attribute_value_indexes.append(a['attribute'].lower(), len(vals) - 1)
           self.attribute_value_indexes[a['attribute'].lower()] = len(vals) - 1
