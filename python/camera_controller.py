# fopd resource
#

from os import getcwd
from datetime import datetime
from time import sleep
from subprocess import check_call, CalledProcessError, run, PIPE, STDOUT
from sys import path, exc_info
from shutil import copyfile
from logging import getLogger
from python.camera_subscribers.make_subscriber import get_camera_subscribers

logger = getLogger('mvp.' + __name__)

def snap() -> 'file_path':

     logger.info('Created new camera image')

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

            return file_location

        else:
           logger.error('fsweb command failed. See following lines for more info:')
           logger.error('---return code: {}'.format(picture_results.returncode))
           logger.error('---stderr: {}'.format(picture_results.stderr.decode('ascii')))
           logger.error('---args: {}'.format(picture_results.args))
           logger.error('---stdout: {}'.format(picture_results.stdout.decode('ascii')))
           return None

     except CalledProcessError as e:
         logger.error('fswebcam call failed with the following results: {}: {}'.format(\
                           exc_info()[0], exc_info()[1]))
         return None
     except:
         logger.error('Camera error: {}: {}'.format(exc_info()[0], exc_info()[1]))
         return None

def make_help(args):
    
    def help():

        prefix = args['name']

        s =     '{}.help()                 - Displays this help page.\n'.format(prefix)
        s = s + "{}.snap()                 - Takes a picture and returns the location of the file.\n".format(prefix)
        
        return s

    return help

def start(app_state, args, b):

    logger.setLevel(args['log_level'])
    logger.info('Starting camera controller.')

    state = {'startup':True}
   
    camera_subscribers = get_camera_subscribers(args['subscribers'])
    
    # Inject your commands into app_state.
    app_state[args['name']] = {} 
    app_state[args['name']]['help'] = make_help(args) 
    app_state[args['name']]['snap'] = snap

    # Don't proceed until all the other threads are up and ready.
    b.wait()    

    while not app_state['stop']:

        this_instant = datetime.now() 
        file_location = None

        for s in camera_subscribers:
            if s.wants_picture(this_instant, state['startup']):
                if file_location == None:
                     file_location = snap()
                s.new_picture(file_location)

        # TBD - put in code to delete any picture files that were created.
      
        state['startup'] = False
        sleep(1)  
