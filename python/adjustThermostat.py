# Based upon code originally witten by Howard Webb.
# Fan actuator controlled by thermometer

from datetime import datetime
#- from logging import getLogger
from python.logger import get_sub_logger 
from sys import exc_info
from time import sleep, time

from config.config import max_air_temperature, fan_controller_temp_sensor 
from python.logData import logData
from python.thermostat import adjustThermostat

#- logger = getLogger('mvp.' + __name__)
logger = get_sub_logger(__name__)

# TBD: Need to add an initializer that turns the fan off when the system powers up or reads it's state and updates the
# the thermostat state with it.
#
# TBD: Need to use the existing si7021 instance that created in the configuration file.  Also teh controller
# algorithm shold be set in the configuration file:
#    (define fan_controller set_temperature)
#       (if current_temp > set_temperature + hysteresis)
#           (fan_on)
#       (else fan_off)
#    ))
#
def start_fan_controller(app_state): 

   logger.info('starting fan controller')

   thermostat_state = {'fan_on':False, 'target_temp':max_air_temperature, 'last_error_ts':time()}

   while not app_state['stop']:

      try:
          current_temp = fan_controller_temp_sensor.getTempC()
          adjustThermostat(thermostat_state, current_temp)  

      except:

          # Limit log entries to one per minute.
          ts = time()
          if ts - thermostat_state['last_error_ts'] > 60:
              logger.error('Failure to get temperature, no sensor found; check pins and sensor: {}, {}'.format(\
                           exc_info()[0], exc_info()[1]))
          thermostat_state['last_error_ts'] = ts

      sleep(1)
