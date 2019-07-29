from shutil import copyfile
from os import path, getcwd
from sys import exc_info

from python.logger import get_sub_logger 

from settings import configuration_directory_location

logger = get_sub_logger(__name__)

def verify_config_file():

   try:

      config_livefile_path = configuration_directory_location + 'config.py'

      if not path.isfile(config_livefile_path):
          
         # ask the user which config file they want.
         print('There is no configuration file present. Run the following commands:\n',
               'python fopd.py -u create_private_key\n',
               'python fopd.py -u create_system\n')
         exit()
         
   except:
       logger.error('Could not verify configuration file: {}, {} exiting ...'.format(\
                    exc_info()[0], exc_info()[1]))
       exit()
