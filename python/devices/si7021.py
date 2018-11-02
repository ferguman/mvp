import threading
import smbus2
import sys
from time import sleep, time

from python.logger import get_sub_logger 

address = 0x40
rh_no_hold = 0xf5
previous_temp = 0xe0

logger = get_sub_logger(__name__)

class si7021(object):

    def __init__(self, config: dict, vals: list):
        self.bus = smbus2.SMBus(1)
        self.config = config

        self.init_sensor_value_list(vals)

        logger.info('i2c sensor si7021. Providing air temperature and humidity. Will use i2c addr {}'.format(address)) 

    def init_sensor_value_list(self, vals: list):

       """ vals is the master list of sensor readings.  It may contain readings 
           from sensors other than this one.  Tack this sensor's readings onto the list
           and remember where in the list the readings are at. """
      
       self.vals = vals
       self.humidity_val_index = None
       self.temperature_val_index = None

       for a in self.config['attributes']:

           self.vals.append(
               {'value_name':a['value_name'], 'type':'environment', 'device_name':self.config['device_name'], 
                'device_id':self.config['device_id'],
                'subject':a['subject'], 'subject_location_id':a['subject_location_id'], 
                'attribute':a['attribute'], 'value':None, 'units':a['units'], 'ts':None})

           if a['attribute'].lower() == 'humidity':
               self.humidity_val_index = len(vals) - 1
           elif a['attribute'].lower() == 'temperature':
               self.temperature_val_index = len(vals) - 1 
           else:
               logger.error('si7021: uknown attribute {}'.format(a['attribute']))

       if self.humidity_val_index == None or self.temperature_val_index == None:
           logger.error('si7021: You must specify humidity and temperature attributes for this device.')

    def update_sensor_readings(self, take_readings=False):

           ts = time()

           self.vals[self.humidity_val_index]['value'] =  self.getHumidity()
           self.vals[self.humidity_val_index]['ts'] = ts 

           self.vals[self.temperature_val_index]['value'] = self.getTempC()
           self.vals[self.temperature_val_index]['ts'] = ts 


    def read_word(self):
        """
        Use I2C ioctl to read Si7021 measurements because SMBus ioctl misbehaves.
        If you just call read_byte() twice, you get the same byte both times. And
        if you try to read a 2 byte buffer here, it also doesn't work right. For
        some reason, 3 bytes seems to be okay.
        """
        msg = smbus2.i2c_msg.read(0x40, 3)
        self.bus.i2c_rdwr(msg)
        msb = ord(msg.buf[0])
        lsb = ord(msg.buf[1])
        checksum = ord(msg.buf[2])
#        print "  si7021 i2c read:", msb, lsb, checksum
        return (msb*256) + lsb

    def write(self, command):
        self.bus.write_byte(address, command)

    def getHumidity(self):
        #- lock = threading.Lock()
        #- with lock:
        self.write(rh_no_hold)
        sleep(0.03)
        percent_rh = self.read_word()
        percent_rh = 125.0/65536.0*percent_rh-6.0
        return percent_rh

    def getTempC(self):
        #- lock = threading.Lock()
        #- with lock:
        self.write(previous_temp)
        temp_c = self.read_word()
        temp_c = 175.72/65536.0*temp_c-46.85
        return temp_c

    def Get(self, attribute: str) -> str:
       try:
          if attribute == "temperature":
             return self.getTempC()
          if attribute == 'humidity':
             return self.getHumidity()

          print('ERROR in si7021. Unknown attribute: {}'.format(attribute))
          return '0'
       except:
          logger.error('Error in Get: {}'.format(sys.exc_info()[0]))

    def test(self):
        'Self test of the object'
        print('\n*** Test SI7021 ***\n')
        print('Temp C: %.2f F' %self.getTempC())
        print('Humidity : %.2f %%' %self.getHumidity())

if __name__=="__main__":
    t=si7021()
    t.test()
    
