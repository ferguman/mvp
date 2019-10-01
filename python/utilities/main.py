from logging import getLogger
from os import path
from uuid import uuid4
from sys import exc_info

from python.data_file_paths import couchdb_local_config_file_directory, configuration_directory_location
from python.random_password import generate_password
from python.encryption.nacl_fop import decrypt, encrypt
from python.logger import get_sub_logger 
from python.repl import start
from python.utilities.create_private_key import create_private_key
from python.utilities.create_system import create_system
from python.utilities.create_service_file import create_service_file

def create_random_uuid():
    """Create a random UUID and print it at the console"""
    print(uuid4())
    return 'OK'

def decrypt_util(pt):
    print(decrypt(pt))
    return 'OK'

def encrypt_util(pt):
    print(encrypt(pt))
    return 'OK'

import fileinput
import re
from subprocess import run 

logger = get_sub_logger('reset_couchdb_passwords')

def change_file_line(fp, line_search_re_str, new_line):

    try:
        line_search_re = re.compile(line_search_re_str)

        changed = False

        logger.info('opening {}'.format(fp))
        with open(fp, mode='r+') as f:
            lines = f.readlines()
            f.seek(0)

            for line in lines:
                if line_search_re.search(line):
                    f.write(new_line)
                    changed = True
                else:
                    # Not the target line so write it back.
                    f.write(line)

            f.truncate()

        return changed
    except:
        logger.error('change_file_line error {}'.format(exc_info()[0], exc_info()[1]))
        return False

def reset_couchdb_passwords(args):

    try:    

        # write the password to the couchdb configuration file
        logger.info('changing couchdb password in local.ini. Reset the couchdb service to take up the new password.')
        # Note: The couchdb service updates the local.ini file to contain the hashed password instead of the plaintext
        #       password. So the admin password is essentially unknown.  
        pwd = generate_password(16)
        pwd_changed = change_file_line(path.join(couchdb_local_config_file_directory, 'local.ini'),
                                                 r'^admin[ |\t]*=', 'admin = {}\n'.format(pwd))
        
        if not pwd_changed:
            logger.error('Unable to reset the couchdb admin password.')
            raise Exception('ERROR: unable to reset couchdb admin password.')
        else:
            logger.info('Writing the couchdb admin password to the config file.')
            change_file_line(path.join(configuration_directory_location, 'config.py'), 
                             r'^couchdb_admin_password_b64_cipher[ |\t]*=', 
                             'couchdb_admin_password_b64_cipher = {}\n'.format(encrypt(pwd.encode('utf-8'))))

            logger.info('Restarting couchdb so that the admin password change is taken up.')
            run('sudo systemctl restart couchdb', shell=True)
            

        # get a random value for the fopd couchdb user password
        fopd_password = generate_password(16)
        #- logger.info('password: {}'.format(fopd_password))

        # TODO: Need to post to the local couchdb server a new password for fopd.

        return True if args['silent'] else 'OK'

    except:
        logger.error('Exception in reset_couchdb_passwords: {}, {}'.format(exc_info()[0], exc_info()[1]))
        return False


def add_utilities(eval_state):

    # Enumerate all possible utility commands
    eval_state['utils'] = {'create_private_key':create_private_key}
    eval_state['utils']['create_system'] = create_system
    eval_state['utils']['create_service_file'] = create_service_file
    eval_state['utils']['create_random_uuid'] = create_random_uuid
    eval_state['utils']['decrypt'] = decrypt_util
    eval_state['utils']['encrypt'] = encrypt_util
    eval_state['utils']['reset_couchdb_passwords'] = reset_couchdb_passwords

#+ TODO: Create a fopd initiliaation routine that does this ->  
#        sudo chown -R couchdb:couchdb couchdb
#        sudo usermod -a -G couchdb pi
#        sudo chmod /fopd/couchdb/etc 775
#        sudo chmod /dopd/couchdb/etc/local.ini 664
#
def execute_utility(cmd, arg_source='namespace', device_name='fopd'):

    #- logger = get_top_level_logger('fopd')
    logger = getLogger(device_name + '.' + 'utility')

    # The reple will see stop = True and exit normally after it processess the start_cmd.
    eval_state = {'stop':True, 'sys':{'cmd':None}}
    eval_state['system'] = {}
    eval_state['config'] = {'device_name':'fopd'}

    add_utilities(eval_state)

    # Run the repl and start with the selected utility. 
    # def start(app_state, silent_mode, barrier, start_cmd=None):
    if arg_source == 'namespace':
       print('utils.' + cmd.utility +'()')
       if cmd.utility == 'encrypt':
          print('input: {}'.format(cmd.utility_input.encode('utf-8')))
          start(eval_state, cmd.silent, None, start_cmd='utils.' + cmd.utility +'({})'.format(cmd.utility_input.encode('utf-8')))
       elif cmd.utility == 'decrypt':
          #TODO: Need to get the decrypt command working
          print('input: {}'.format(cmd.utility_input))
          start(eval_state, cmd.silent, None, start_cmd='utils.' + cmd.utility +'({})'.format(cmd.utility_input))
       else:
          start(eval_state, cmd.silent, None, start_cmd='utils.' + cmd.utility +'()')
    elif arg_source == 'dictionary':
        return start(eval_state, cmd['args']['silent'], None, start_cmd='utils.' + cmd['cmd'] + '({})'.format(cmd['args']))
        #- return True
    else:
        raise Exception('error, unknown arg_source')

    exit()
