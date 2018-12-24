from os import path, getcwd, mkdir

from python.encryption.nacl_utils import create_random_key

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

def create_config_directory() -> 'path_to_config_file':

    cp = path.join(getcwd(), 'config')
    if not path.isdir(cp):
        print('Creating directory named config at {}'.format(cp))
        mkdir(cp)

    return cp


