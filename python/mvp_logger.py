from logging import getLogger, Formatter, INFO, DEBUG 
from logging.handlers import RotatingFileHandler
from os import getcwd

# TBD:  Move the logging configuration to a dictionary stored in a configuration file.
# On linux use tail -F (translates as tail --follow=name --retry) to follow the 
# rotating log. tail -f stops following when the log gets rotated out from under it.
#
# This logger currenlty rotates based upon file size. Python also supports timed based 
# rotation.
#

def get_logger():

   logger = getLogger('mvp')
   logger.setLevel(INFO)
   handler = RotatingFileHandler(getcwd() + '/logs/mvp.log', maxBytes=10*1000*1000,\
                                 backupCount=5)
   formatter = Formatter(fmt='%(asctime)s %(levelname)s %(name)s:%(message)s', 
                             datefmt='%Y-%m-%d %I:%M:%S %p %Z')
   handler.setFormatter(formatter)
   logger.addHandler(handler)

   return logger
