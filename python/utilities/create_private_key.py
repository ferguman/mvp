from os import path, getcwd, mkdir

from python.encryption.nacl_utils import create_random_key
from python.utilities.prompt import prompt

def create_private_key():
    """ Create a private key then put it in a private key file """

    print('This utility will ask you for your private key. It will give you the option of supplying')
    print('your own private key or having the system generate a random private key for you.')
    print('It will then create a binary file containing this private key.')
    print('The file will be placed at config/private_key.\n')
    print('Enter yes to proceed, no to exit')
    
    cmd = input('fopd: ')

    if cmd.lower() != 'yes':
        return 'CANCELED'

    cp = create_config_directory()

    pkfp = cp + '/private_key'
    if path.isfile(pkfp):
        print('WARNING: A private key file already exists: {}.\n'.format(pkfp),
              'If you proceed this file will be deleted. Any key stored in this file will be lost\n',
              'and thus any date encrypted to that key such as device configuration data will be lost.\n',
              'Enter yes to proceed, no to exit')
        cmd = input('fopd: ')

        if cmd.lower() != 'yes':
            return 'CANCELED'

    # ask the user if they want to use their own private key or generate a random one.
    vals = ('private_key',)
    prompts = {'private_key':'If you wish to supply your own private key then please enter it here\n'+\
                             "as a 32 byte array (e.g. b'&\xfeabd\x32 ....'). Enter random in this\n" +\
                             'field to have the system generate a random key for you.'}

    #TODO - It is dangerous to eval user input. Try to refactor to safer code.
    generators = {'private_key':{'random':lambda s: create_random_key(), 'default':lambda s: eval(s)}}

    key = prompt(vals, prompts, generators)['private_key']
    print(type(key))
    print(key)

    with open(pkfp, 'wb') as f:

        f.write(key)

    return 'OK'

def create_config_directory() -> 'path_to_config_file':

    cp = path.join(getcwd(), 'config')
    if not path.isdir(cp):
        print('Creating directory named config at {}'.format(cp))
        mkdir(cp)

    return cp


