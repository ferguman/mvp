import threading
import smbus2

from sys import exc_info
from time import sleep, time
from timeit import default_timer as timer 

from python.devices.I2c_slave import I2c_slave
from python.logger import get_sub_logger 

# Use the default address if none is supplied via the configuration
# The am2315 has one built in address (0xB8)
default_i2c_address = 0xB8

#- rh_no_hold = 0xf5
#- previous_temp = 0xe0

#TODO - This sensor class is not functional. It needs to be completed.

logger = get_sub_logger(__name__)

class am2315(I2c_slave):

    def initialize(self) -> bool:

        start_time = timer()

        logger.info('initializing am2315 sensor (air temperature and humidity)') 

        if not self.i2c_addr:
            self.i2c_addr = default_i2c_address
            logger.warning('No i2c address was supplied by the system. Will use {} (hex), {} (decimal)'.format(hex(default_i2c_address), default_i2c_address))
        else:
            logger.info('i2c address configured to {} (hex), {} (decimal)'.format(hex(self.i2c_addr), self.i2c_addr))

        # Store the time of occurence and error count for each type of error that has the potential to flood
        # the log file. 
        humidity_read_error_id = 0
        temp_read_error_id = 1

        try:
            #+ self.update_sensor_readings()
            #+ logger.info('Initial si7021 sensor readings -> temp: {}, humidity: {}'.format(
                #+ self.vals[self.attribute_value_indexes['temperature']]['value'], 
                #+ self.vals[self.attribute_value_indexes['humidity']]['value']))
                return False;
        except:
            logger.error('am2315 sensor failed to initilize: {}, {}'.format(exc_info()[0], exc_info()[1]))
            return False

        logger.info('am2315 sensor initialized successfully in {:.3f} seconds'.format(timer() - start_time))

        return True 

    def update_sensor_readings(self, take_readings=False):

        ts = time()

        try:               
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
                    logger.error('si7021 sensor - unknown attribute value {}, check the configuration'.format(k))
        except:
            logger.error('cannot read am2315 sensor: {}, {}'.format(exc_info()[0], exc_info()[1]))
            # Blank the sensor readings
            for k,v in self.attribute_value_indexes.items():
                self.vals[v]['value'] = None 


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
