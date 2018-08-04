from time import sleep, time
from logging import getLogger

logger = getLogger('mvp.' + __name__)

def time_to_sample(interval, state):

   if interval <= 0 or interval > 86400:
      logger.error('The data_logger_sample_interval must be '
                 + 'set to a value between 1 and 86400. BTW: 86400 seconds is 24 hours.')
      return False

   if state['next_sample_time'] <= time():
      state['next_sample_time'] = time() + interval 
      return True
   else:
      return False
    
def start(app_state, args):
   
    logger.setLevel(args['log_level'])
    logger.info('starting data logger')

    # Set state so that a sample is taken on startup.
    state = {'next_sample_time':0}
    
    while not app_state['stop']:

       if time_to_sample(args['sample_interval'], state):

            logger.info('Logging sensor readings')
         
            for r in app_state['sensor_readings']:
                logger.info('sensor reading ...')
      
       sleep(1)
