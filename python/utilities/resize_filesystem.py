from subprocess import run 
from sys import exc_info

from python.logger import get_sub_logger 

logger = get_sub_logger(__name__)

def resize_filesystem(args):
    try:

        #TODO: Need to put a check that this command is supported - ie. running
        #      on Linux and using ext4 file system.
        logger.info('resizing {} file system'.format(args['device_name']))
        res = run('sudo resize2fs {}'.format(args['device_name']), capture_output=True, shell=True)
        if len(res.stdout) > 0:
            logger.info('resize result: {}'.format(res.stdout.decode('utf-8')))
        if len(res.stderr) > 0:
            logger.error('resize error: {}'.format(res.stderr.decode('utf-8')))

        return True if args['silent'] else 'OK'

    except:
        logger.error('Exception in resize_filesystem: {}, {}'.format(exc_info()[0], exc_info()[1]))
        return False if args['silent'] else 'ERROR'
