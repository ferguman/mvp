# fopd resource
#

from os import getcwd
from datetime import datetime
from time import sleep
from subprocess import check_call, CalledProcessError, run, PIPE, STDOUT
from sys import path, exc_info
from shutil import copyfile
from threading import Lock

from python.camera_subscribers.make_subscriber import get_camera_subscribers
from python.logger import get_sub_logger 

logger = get_sub_logger(__name__)

camera_lock = Lock()

def snap(repl, pose_on_cmd, pose_off_cmd) -> 'file_path':

    # Wait for camera to become available.
    camera_lock.acquire()

    try:
        logger.info('Creating new camera image')

        # Tell the light controller to pose for a picture
        repl(pose_on_cmd)

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
    finally:
        # TODO: Track down the official documentation on this and replace the following with it.
        # According to someone on stack overflow: The finally clause is also executed “on the way out” 
        # when any other clause of the try statement is left via a break, continue or return statement. So
        # even though there are return statements in the code above the Python interpretter should still
        # execute the next block of code before returning to the caller.
        camera_lock.release()
        
        # Tell the light controller to go back to it's normal operation
        repl(pose_off_cmd)

def make_snap(repl, pose_on_cmd, pose_off_cmd):

    def snap_cmd():
        return snap(repl, pose_on_cmd, pose_off_cmd)

    return snap_cmd


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
    app_state[args['name']]['snap'] = make_snap(app_state['sys']['cmd'], args['pose_on_cmd'], args['pose_off_cmd'])

    # Don't proceed until all the other threads are up and ready.
    b.wait()    

    while not app_state['stop']:

        this_instant = datetime.now() 
        file_location = None

        for s in camera_subscribers:
            if s.wants_picture(this_instant, state['startup']):
                if file_location == None:
                    file_location = snap(app_state['sys']['cmd'], args['pose_on_cmd'], args['pose_off_cmd'])
                s.new_picture(file_location)

        # TODO - put in code to delete any picture files that were created. Keep in mind that this assumes that 
        #        the s's above don't return from the new_picture method till they are done with the file.  A 
        #        more sophisticated garbage collection scheme is required if the listeners need the file
        #        for the an arbitrary amount of time after the new_picture method returns.  One way maybe is to
        #        to create a queue for each listener and to not delete files that are still in one of the queues.
      
        state['startup'] = False
        sleep(1)  

    logger.info('exiting the camera controller thread')
