from datetime import datetime
from subprocess import check_call, CalledProcessError
from sys import path
from time import sleep, time

from config.config import charting_interval, couchdb_location_url, chart_list
from python.generate_chart import generate_chart
from python.logger import get_sub_logger 

logger = get_sub_logger(__name__)

def start(app_state, args, b):

   logger.info('starting web chart generator controller')
   logger.setLevel(args['log_level'])

   app_state['sys']['chart_list'] = args['chart_list']

   # Set the intial timestamp to 0 thus forcing a web chart generation at start up.
   state = {'last_charting_ts':0, 'last_chart_generation_date':None}

   # Let the system know that you are good to go.
   b.wait()

   while not app_state['stop']:

      this_ts = time()

      if (this_ts - state['last_charting_ts'])/60 > charting_interval:

         # Generate the charts
         # Figure out how the script directory is getting put in the path. Or in other words
         # how does the system find this command file.
         # Need to make location of the render.sh script a config file setting.

         try:

            #- for chart_info in chart_list:
            for chart_info in args['chart_list']:

               #- generate_chart(couchdb_location_url, chart_info, app_state)
               generate_chart(args['couchdb_location_url'], chart_info, logger)

            state['last_charting_ts'] = this_ts
            state['last_chart_generation_date'] = datetime.now()

            logger.info('Created new web charts.')

         except CalledProcessError as e:
            logger.error('render.sh call failed with the following results:{}'.format(charting_results))

      sleep(1)

   logger.info('shutting down chart generator')
