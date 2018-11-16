import threading
from os import path, getcwd, mkdir
from python.logger import get_top_level_logger
from python.repl import start
from python.encryption.nacl_utils import create_random_key

logger = get_top_level_logger('fopd')

def create_config_directory() -> 'path_to_config_file':

    cp = path.join(getcwd(), 'config')
    if not path.isdir(cp):
        print('Creating directory named config at {}'.format(cp))
        mkdir(cp)

    return cp


def select_system():
    """ Ask the user what hardware their software will be run on """

    print('In order to setup a system configuration file you must specify what',
          'type of hardware your system is running on.\n',
          '\nchoose one of the following:\n',
          'download -> if you want to download a sytem configuration\n',
          'fc1      -> for openag foodcomputer version 1\n',
          'fc2      -> for openag food computer version 2\n',
          'mvp      -> for futureag mvp food computer\n',
          'custom   -> if you wish to configure your system by hand.\n',
          'exit     -> to exit this utility.')

    cmd = input('fopd: ')

    if not cmd.lower() == 'fc1':
        print('this utility only supports fc1 at this time. will exit')
        return 'CANCELLED'

    sys_file_path = cp + '/system.py'
    if path.isfile(sys_file_path):
        print('WARNING: A private key file already exists: {}.\n'.format(pkfp),
              'If you proceed this file will be deleted. Any key stored in this file will be lost\n',
              'and thus any date encrypted to that key such as device configuration data will be lost.\n',
              'Enter yes to proceed, no to exit')
        cmd = input('fopd: ')

        if cmd.lower() != 'yes':
            return 'CANCELED'

    cp = create_config_directory()

    return 'OK'

def create_private_key():
    """ Create a private key then put it in a private key file """

    print('This utility will create a new private key and then create a file containing this private key.')
    print('The file will be placed at config/private_key.py.\n')
    print('Enter yes to proceed, no to exit')
    
    cmd = input('fopd: ')

    if cmd.lower() != 'yes':
        return 'CANCELED'

    cp = create_config_directory()

    pkfp = cp + '/private_key.py'
    if path.isfile(pkfp):
        print('WARNING: A private key file already exists: {}.\n'.format(pkfp),
              'If you proceed this file will be deleted. Any key stored in this file will be lost\n',
              'and thus any date encrypted to that key such as device configuration data will be lost.\n',
              'Enter yes to proceed, no to exit')
        cmd = input('fopd: ')

        if cmd.lower() != 'yes':
            return 'CANCELED'
        
    with open(pkfp, 'w') as f:

        c = 'nsk_b64 = {}'.format(create_random_key())
        f.write(c)

    return 'OK'


def execute_utility(args):

    eval_state = {'stop':True, 'sys':{'cmd':None}}
    eval_state['utils'] = {'create_private_key':create_private_key}
    eval_state['utils']['select_system'] = select_system
    eval_state['system'] = {}
    eval_state['config'] = {'device_name':'fopd'}

    start(eval_state, args.silent, 'utils.'+ args.utility +'()')

    exit()
