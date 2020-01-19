import threading
import smbus2

from sys import exc_info
from time import sleep, time
from timeit import default_timer as timer 

from python.devices.I2c_slave import I2c_slave
from python.logger import get_sub_logger 

# Use the default address if none is supplied via the configuration
default_i2c_address = 0x40

rh_no_hold = 0xf5
previous_temp = 0xe0

logger = get_sub_logger(__name__)

#- class si7021(object):
class si7021(I2c_slave):

    def initialize(self) -> bool:

        #TODO - Need to add a try except block around this code to catch exceptions

        start_time = timer()
        logger.info('initializing si7021 sensor (air temperature and humidity)') 

        if not self.i2c_addr:
            self.i2c_addr = default_i2c_address
            logger.warning('No i2c address was supplied by the system. Will use {} (hex), {} (decimal)'.format(hex(default_i2c_address), default_i2c_address))
        else:
            logger.info('i2c address configured to {} (hex), {} (decimal)'.format(hex(self.i2c_addr), self.i2c_addr))

        # Store the time of occurence and error count for each type of error that has the potential to flood
        # the log file. 
        humidity_read_error_id = 0
        temp_read_error_id = 1

        self.update_sensor_readings()

        logger.info('si7021 sensor initialized successfully in {:.3f} seconds'.format(timer() - start_time))

        return True 

    def update_sensor_readings(self, take_readings=False):

           ts = time()
               
           h = self.getHumidity()
           t = self.getTempC()

           for k,v in self.attribute_value_indexes.items():
               if k == 'humidity':
                   self.vals[v]['value'] = '{:+.1f}'.format(h)
                   self.vals[v]['ts'] = ts 
               elif k == 'temperature':
                   self.vals[v]['value'] = '{:+.1f}'.format(t)
                   self.vals[v]['ts'] = ts 
               else:
                   logger.error('unknown attribute value {}, check the configuration'.format(k))
               

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
        self.bus.write_byte(self.i2c_addr, command)

    def getHumidity(self):
        try: 
            self.write(rh_no_hold)
            sleep(0.03)
            percent_rh = self.read_word()
            percent_rh = 125.0/65536.0*percent_rh-6.0
            return percent_rh
        except:
            logger.error('cannot read humidity from sensor: {}, {}'.format(exc_info()[0], exc_info()[1]))

    def getTempC(self):
        try:
            self.write(previous_temp)
            temp_c = self.read_word()
            temp_c = 175.72/65536.0*temp_c-46.85
            return temp_c
        except:
            logger.error('cannot read temperature from sensor: {}, {}'.format(exc_info()[0], exc_info()[1]))

    def Get(self, attribute: str) -> str:
       try:
          if attribute == "temperature":
             return self.getTempC()
          if attribute == 'humidity':
             return self.getHumidity()

          print('ERROR in si7021. Unknown attribute: {}'.format(attribute))
          return '0'
       except:
          logger.error('Error in Get: {}'.format(exc_info()[0]))

    def test(self):
        'Self test of the object'
        print('\n*** Test SI7021 ***\n')
        print('Temp C: %.2f F' %self.getTempC())
        print('Humidity : %.2f %%' %self.getHumidity())
