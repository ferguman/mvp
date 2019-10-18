# fopd resource

from os import getcwd, path as os_path
from datetime import datetime
from time import sleep
from subprocess import check_call, CalledProcessError, run, PIPE, STDOUT
from sys import path, exc_info
from shutil import copyfile
from threading import Lock

from python.data_file_paths import camera_image_directory
from python.camera_subscribers.make_subscriber import get_camera_subscribers
from python.logger import get_sub_logger 
from python.LogFileEntryTable import LogFileEntryTable

logger = get_sub_logger(__name__)
log_entry_table = LogFileEntryTable(60*60)

camera_lock = Lock()

def snap(repl: 'fop repl monitor', pose_on_cmd: 'fop command', pose_off_cmd: 'fop command') -> 'file_path':

    # Wait for camera to become available.
    camera_lock.acquire()

    try:
        logger.info('Creating new camera image')

        # Tell the light controller to pose for a picture
        repl(pose_on_cmd)

        file_name = '{:%Y%m%d_%H_%M_%S}.jpg'.format(datetime.utcnow())
        file_location = os_path.join(camera_image_directory, file_name)
        #- file_location = '{}{}'.format(getcwd() + '/pictures/', file_name) 

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


def make_help(args):
    
    def help():

        prefix = args['name']

        s =     '{}.help()                 - Displays this help page.\n'.format(prefix)
        s = s + "{}.snap()                 - Takes a picture and returns the location of the file.\n".format(prefix)
        s = s + "{}.show_subs()            - Display a list of the Camera Subscribers.\n".format(prefix)
        s = s + "{}.update(sub)            - Takes a picture and sends it to the subscriber indicated by target.\n".format(prefix)
        s = s + "                          - Example: {}.update('LocalWebServer')".format(prefix)
        
        return s

    return help

def make_update(app_state, args, camera_subscribers: list):

    def update(sub):
        logger.info('got here')

        for s in camera_subscribers:
            if s.name.lower() == sub.lower():          
                file_location = snap(app_state['sys']['cmd'], args['pose_on_cmd'], args['pose_off_cmd'])
                if file_location == None:
                    return 'Cannot take a picture'
                s.new_picture(file_location)
                return 'OK'

        return 'Cannot find the subscriber. Try running {}.show_subs()'.format(args['name'])

    return update


def make_show_subs(camera_subscribers):

    def show_subs():
        s = ''
        if len(camera_subscribers) > 0:
            for sub in camera_subscribers:
                s = s + '{}\n'.format(sub.name)
            return s
        else:
            return 'there are no camera subscribers\n'

    return show_subs


def start(app_state, args, b):

    logger.setLevel(args['log_level'])
    logger.info('Starting camera controller.')

    state = {'startup':True, 'daily_archive_has_run':False}
   
    camera_subscribers = get_camera_subscribers(args['subscribers'])

    # Inject your commands into app_state.
    app_state[args['name']] = {} 
    app_state[args['name']]['help'] = make_help(args) 
    app_state[args['name']]['snap'] = lambda: snap(app_state['sys']['cmd'], args['pose_on_cmd'], args['pose_off_cmd'])
    app_state[args['name']]['show_subs'] = make_show_subs(camera_subscribers) 
    app_state[args['name']]['update'] = make_update(app_state, args, camera_subscribers) 

    # Don't proceed until all the other threads are up and ready.
    b.wait()    

    while not app_state['stop']:

        this_instant = datetime.now() 
        file_location = None

        for s in camera_subscribers:
            if s.wants_picture(this_instant, state['startup']):
                if file_location == None:
                    file_location = snap(app_state['sys']['cmd'], args['pose_on_cmd'], args['pose_off_cmd'])
                    if file_location == None:
                        logger.error('Cannot take a picture')
                        break
                try:
                   s.new_picture(file_location)
                except:
                   logger.error('camera subscriber exception occured: {}, {}'.format(exc_info()[0], exc_info()[1]))
            #+ elif s.wants_periodic_calls:
            #+    s.periodic_call()

        # NOTE syntax of delete info in config file ->  'delete_args':{'max_day_age': 2},
        # Delete old pictures every morning at 9 am local time.
        if 'delete_args' in args:
            try:
                if this_instant.hour == 9:
                    if not state['daily_archive_has_run']:
                        logger.info('will delete pictures older than {} days'.format(args['delete_args']['max_day_age']))
                        run('find /data/fopd/pictures -name "*.*" -type f -mtime {} -exec rm -f {{}} \;'.format(
                            args['delete_args']['max_day_age']), shell=True)
                        state['daily_archive_has_run'] = True
                else:
                    state['daily_archive_has_run'] = False 
            except:
                log_entry_table.add_log_entry(logger.error, 
                    'camera exception while deleting old pictures: {}, {}'.format(exc_info()[0], exc_info()[1]))

        state['startup'] = False
        sleep(1)  

    logger.info('Exiting the camera controller thread')
