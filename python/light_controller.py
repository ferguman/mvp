# This is a fopd resource
#
# it requires an on/off light controller -> eg. controller('on') and controller('off')
#
from datetime import datetime
#- from logging import getLogger
from time import sleep

from python.logger import get_sub_logger 
#- logger = getLogger('mvp.' + __name__)
logger = get_sub_logger(__name__)

def run_controller(light_state, lc, program):

   this_update_time = datetime.now().time()

   # If we've wrapped around midnight then bring the last update time forward.
   # Set times are specified with a resolution of 1 minute so this "bring forward"
   # operation should not skip over any set times.
   # TBD Need to test this peice of code. Also we could skip exit the controller on all
   # calls other than those that cross a minute boundary.
   if this_update_time < light_state['last_update']:
      light_state['last_update'] = datetime.strptime('12:00 AM',  '%I:%M %p').time()

   for x in program:

      set_time = datetime.strptime(x[1], '%I:%M %p').time()

      #logger.debug('command:{}, this_update_time:{}, set_time:{}, last_upate:{}, Light On:{}'.format(
      #             x, this_update_time, set_time, light_state['last_update'], light_state['light_on']))

      if light_state['last_update'] <= set_time and this_update_time >= set_time:

         if x[0] == 'on':
            lc('on')
            light_on = True
         else:
            if x[0] == 'off':
               lc('off')
               light_on = False
            else:
               logging.error('ERROR. Illegal value ({}) for light command.'.format(x[0]))
               return {'error':True, 'light_on':light_state['light_on'], 'last_update':this_update_time}

         logger.info('{:%Y-%m-%d %H:%M:%S} Turning light {}.'.format(datetime.now(), x[0])) 
         return {'error':False, 'light_on':light_on, 'last_update':this_update_time}

   #at this point you haven't 'fired' on any commands.
   return {'error':False, 'light_on':light_state['light_on'], 'last_update':this_update_time}

def start(app_state, args, b):

    logger.setLevel(args['log_level'])
    logger.info('Starting light controller.')

    # Don't proceed until the actuator is up and running.
    b.wait()    

    # light_state - get the actuator command function:w
    lc = app_state[args['actuator_resource']][args['actuator_cmd']]
    lc('off')
    light_state = {'error':False, 'light_on':False, 'last_update':datetime.now().time()}

    while not app_state['stop']:

        light_state = run_controller(light_state, lc, args['program'])
        
        sleep(1)

    logger.info('light controller thread stopping.')
