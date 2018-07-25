from os import getcwd
from datetime import datetime
from time import sleep
from subprocess import check_call, CalledProcessError, run, PIPE, STDOUT
from sys import path, exc_info
from shutil import copyfile
from logging import getLogger
#- from python.file_uploader import upload_camera_image

from config.config import camera_controller_program, camera_subscribers

logger = getLogger('mvp.' + __name__)

def is_picture_minute(this_instant):

   if camera_controller_program[0] == 'hourly':
      if this_instant.time().minute == camera_controller_program[1]:
         return True
     
   return False

def start_camera_controller(app_state):

   logger.info('Starting camera controller.')

   state = {'hour_of_last_try':None, 
            'startup':True}

   while not app_state['stop']:

      current_state = state

      this_instant = datetime.now() 

      if state['startup'] == True or \
          ((state['hour_of_last_try'] != this_instant.time().hour) and\
          is_picture_minute(this_instant)):
        
         logger.info('Created new camera image')

         state['hour_of_last_try'] = this_instant.time().hour
         state['startup'] = False

         file_name = '{:%Y%m%d_%H_%M_%S}.jpg'.format(datetime.utcnow())
         file_location = '{}{}'.format(getcwd() + '/pictures/', file_name) 

         camera_shell_command = 'fswebcam -r 1280x720 --no-banner --timestamp "%d-%m-%Y %H:%M:%S (%Z)"'\
                                + ' --verbose  --save {}'.format(file_location)
         logger.debug('Preparing to run shell command: {}'.format(camera_shell_command))

         try:
            # Take the picture
            # Figure out if you can suppress fswebcam's output or take the picture using native python code.
            #- picture_results = check_call(camera_shell_command, shell=True)
            #TBD - refactor to run as shell=False. This will make the sytem safer against injection
            # attacks.
            picture_results = run(camera_shell_command, stdout=PIPE, stderr=PIPE, shell=True, check=False)

            if picture_results.returncode == 0:
                
                if len(picture_results.stderr) != 0:
                    logger.debug('---stderr: {}: '.format(picture_results.stderr.decode('ascii')))

                logger.debug('fsweb command success. See the following lines for more info:')
                logger.debug('---return code: {} ...'.format(picture_results.returncode))
                logger.debug('---args: {} ...'.format(picture_results.args))
                logger.debug('---stdout: {}'.format(picture_results.stdout.decode('ascii')))

                # Alert all the camera subscribers to the new picture file
                for s in camera_subscribers:
                    s.new_picture(file_location)

            else:
               logger.error('fsweb command failed. See following lines for more info:')
               logger.error('---return code: {}'.format(picture_results.returncode))
               logger.error('---stderr: {}'.format(picture_results.stderr.decode('ascii')))
               logger.error('---args: {}'.format(picture_results.args))
               logger.error('---stdout: {}'.format(picture_results.stdout.decode('ascii')))

         except CalledProcessError as e:
             logger.error('fswebcam call failed with the following results: {}: {}'.format(\
                           exc_info()[0], exc_info()[1]))
         except:
             logger.error('Camera error: {}: {}'.format(exc_info()[0], exc_info()[1]))
            
      sleep(1)  
