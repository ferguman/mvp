from shutil import copyfile
from os import path, getcwd
from sys import exc_info

from python.logger import get_sub_logger 

logger = get_sub_logger(__name__)

def verify_config_file():

   try:

      config_livefile_path = getcwd() + '/config/config.py'

      if not path.isfile(config_livefile_path):
          
         # ask the user which config file they want.
         print('There is no configuration file present. You are probably running this software for the first time.')
         print('Specify which configuration file type (either mvp or fc1) that you wish to use.')

         while True:

             cmd = input('fopd:')

             if cmd == 'mvp':
                 config_defaultfile_path = getcwd() + '/python/config_default_mvp.py'
                 break

             if cmd == 'fc1':
                 config_defaultfile_path = getcwd() + '/python/config_default_fc1.py'
                 break

             if cmd != 'mvp' and cmd != 'fc1':
                 logger.error('Illegal configuration file specified: {}'.format(cmd))
                 print('Please specify either mvp or fc1. Or manually create a custom configuration file.')
        
         logger.info('No configuration file was found. Reverting to the mvp configuration file.')
         copyfile(config_defaultfile_path, config_livefile_path)

   except:
       logger.error('Could not verify configuration file: {}, {} exiting ...'.format(\
                    exc_info()[0], exc_info()[1]))
       exit()

def verify_web_config_file():

      try:

         web_server_defaultfile_path = getcwd() + '/python/web_server_config_default.py'
         web_server_livefile_path = getcwd() + '/config/web_server_config.py'

         if not path.isfile(web_server_livefile_path):
            print('No web configuration file was found. Reverting to the default'
                  + ' configuration file.')
            copyfile(web_server_defaultfile_path, web_server_livefile_path )

      except:
         print('Could not verify web configuration file: {}, {} exiting ...'.format(\
               exc_info()[0], exc_info()[1]))
         exit()
