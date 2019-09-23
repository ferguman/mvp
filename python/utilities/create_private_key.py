#- from os import path, getcwd, mkdir
from os import path, getcwd, system

from python.encryption.nacl_utils import create_random_key
from python.term_text_colors import green, red
from python.utilities.prompt import prompt

from python.data_file_paths import configuration_directory_location

def create_private_key():
    """ Create a private key then put it in a private key file """

    print('This utility will ask you for your private key. It will give you the option of supplying')
    print('your own private key or having the system generate a random private key for you.')
    print('It will then create a binary file containing this private key.')
    print('The file will be placed at {}private_key.\n'.format(configuration_directory_location))
    print('Note that if you already have a private key file then exit this utility and copy the file')
    print('to {}private_key. Note that encrypted information stored in the configuration file is'.format(configuration_directory_location))
    print('decrypted using this private key.\n')

    print('Enter {} to proceed, {} to to exit.'.format(red('yes'), red('exit')))
    
    cmd = input(green('fopd: '))

    if cmd.lower() != 'yes':
        return 'CANCELED'

    cp = create_config_directory()

    pkfp = cp + '/private_key'
    if path.isfile(pkfp):
        print('WARNING: A private key file already exists: {}.\n'.format(pkfp),
              'If you proceed this file will be deleted. Any key stored in this file will be lost\n',
              'and thus any date encrypted to that key such as device configuration data will be lost.\n',
              'Enter {} to proceed, {} to exit'.format(red('yes'), red('exit')))
        cmd = input('fopd: ')

        if cmd.lower() != 'yes':
            return 'CANCELED'

    # ask the user if they want to use their own private key or generate a random one.
    vals = ('private_key',)
    prompts = {'private_key':'If you wish to supply your own private key then please enter it here\n'+\
                             "as a 32 byte array (e.g. {}). Enter {} \n".format(red(b'&\xfeabd\x32 ....'), red('random')) +\
                             'to have the system generate a random key for you.'}

    #TODO - It is dangerous to eval user input. Try to refactor to safer code.
    generators = {'private_key':{'random':lambda s: create_random_key(), 'default':lambda s: eval(s)}}

    key = prompt(vals, prompts, generators)['private_key']
    # debug - print(type(key))
    # debug - print(key)

    with open(pkfp, 'wb') as f:

        f.write(key)

    return 'OK'

def create_random_uuid():
    """Create a random UUID and print it at the console"""
    print(uuid4())

def create_config_directory() -> 'path_to_config_file':

    cp = path.join(configuration_directory_location)
    if not path.isdir(cp):
        print('Creating directory named config at {}'.format(cp))
        system('sudo mkdir {}'.format(cp))
        system('sudo chown pi:pi {}'.format(cp))
        #- mkdir(cp)

    return cp
