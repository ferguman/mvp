from logging import getLogger
#- from os import path
from uuid import uuid4
#- from sys import exc_info

#- from python.data_file_paths import couchdb_local_config_file_directory, configuration_directory_location
#- from python.random_password import generate_password
from python.encryption.nacl_fop import decrypt, encrypt
#- from python.logger import get_sub_logger 
from python.repl import start
from python.utilities.reset_couchdb_passwords import reset_couchdb_passwords
from python.utilities.create_private_key import create_private_key
from python.utilities.create_system import create_system
from python.utilities.create_service_file import create_service_file
from python.utilities.set_wifi_mode import set_wifi_mode

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

#- logger = get_sub_logger('reset_couchdb_passwords')
def add_utilities(eval_state):

    # Enumerate all possible utility commands
    eval_state['utils'] = {'create_private_key':create_private_key}
    eval_state['utils']['create_system'] = create_system
    eval_state['utils']['create_service_file'] = create_service_file
    eval_state['utils']['create_random_uuid'] = create_random_uuid
    eval_state['utils']['decrypt'] = decrypt_util
    eval_state['utils']['encrypt'] = encrypt_util
    eval_state['utils']['reset_couchdb_passwords'] = reset_couchdb_passwords
    eval_state['utils']['set_wifi_mode'] = set_wifi_mode 


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
