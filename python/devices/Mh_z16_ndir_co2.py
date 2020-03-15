import smbus2
from time import sleep, clock, time
from timeit import default_timer as timer 

from python.devices.I2c_slave import I2c_slave
from python.logger import get_sub_logger 

logger = get_sub_logger(__name__)

class Mh_z16_ndir_co2(I2c_slave):

    cmd_measure = [0xFF,0x01,0x9C,0x00,0x00,0x00,0x00,0x00,0x63]
    ppm         = 0

    IOCONTROL   = 0X0E << 3
    FCR         = 0X02 << 3
    LCR         = 0X03 << 3
    DLL         = 0x00 << 3
    DLH         = 0X01 << 3
    THR         = 0X00 << 3
    RHR         = 0x00 << 3
    TXLVL       = 0X08 << 3
    RXLVL       = 0X09 << 3


    def initialize(self):

        #TODO - Add code to check that the configuration matches this sensors
        #       capabilities.

        start_time = timer()

        logger.info('initializing MH-Z16 Co2 Sensor at address {} (hex), {} (decimal)'.format(hex(self.i2c_addr), self.i2c_addr))

        try:
            self.write_register(self.IOCONTROL, 0x08)
        except IOError:
            pass

        trial = 10

        for i in range(trial):
            try:
                self.write_register(self.FCR, 0x07)
                self.write_register(self.LCR, 0x83)
                self.write_register(self.DLL, 0x60)
                self.write_register(self.DLH, 0x00)
                self.write_register(self.LCR, 0x03)

                logger.info('MH-Z16 Co2 Sensor initialized successfully in {:.3f} seconds'.format(timer() - start_time))
                return True
            # except IOError:
            except:
                logger.error('MH-Z16 Co2 Sensor failed to initialize after {:.3f} seconds'.format(timer() - start_time))
                return False 

        logger.error('MH-Z16 Co2 Sensor failed to initialize after {} trials and {:.3f} seconds'.format(trial, timer() - start_time))
        return False

    def update_sensor_readings(self):
        try:
            ts = time()
            
            self.write_register(self.FCR, 0x07)
            self.send(self.cmd_measure)
            sleep(0.01)

            self.ppm = None
            self.parse(self.receive())
            if self.ppm:
               self.vals[self.attribute_value_indexes['co2']]['value'] = '{:+.1f}'.format(self.ppm)
            else:
               self.vals[self.attribute_value_indexes['co2']]['value'] = None

            self.vals[self.attribute_value_indexes['co2']]['ts'] = ts 

        #- except IOError:
        except:
            logger.error('cannot read MH-Z16 Co2 sensor: {}, {}'.format(exc_info()[0], exc_info()[1]))
            # Blank the sensor readings
            self.vals[self.attribute_value_indexes['co2']]['value'] = None


    def parse(self, response):
        checksum = 0

        if len(response) < 9:
            return

        for i in range (0, 9):
            checksum += response[i]

        if response[0] == 0xFF:
            if response[1] == 0x9C:
                if checksum % 256 == 0xFF:
                    self.ppm = (response[2]<<24) + (response[3]<<16) + (response[4]<<8) + response[5]

    def read_register(self, reg_addr):
        sleep(0.001)
        return self.bus.read_byte_data(self.i2c_addr, reg_addr)

    def write_register(self, reg_addr, val):
        sleep(0.001)
        self.bus.write_byte_data(self.i2c_addr, reg_addr, val)

    def send(self, command):
        if self.read_register(self.TXLVL) >= len(command):
            self.bus.write_i2c_block_data(self.i2c_addr, self.THR, command)

    def receive(self):
        n     = 9
        buf   = []
        start = clock()

        while n > 0:
            rx_level = self.read_register(self.RXLVL)

            if rx_level > n:
                rx_level = n

            buf.extend(self.bus.read_i2c_block_data(self.i2c_addr, self.RHR, rx_level))
            n = n - rx_level

            if clock() - start > 0.2:
                break

        return buf
