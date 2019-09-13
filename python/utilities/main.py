from uuid import uuid4

from python.encryption.nacl_fop import decrypt, encrypt
from python.logger import get_top_level_logger
from python.repl import start
from python.utilities.create_private_key import create_private_key
from python.utilities.create_system import create_system
from python.utilities.create_service_file import create_service_file

#-logger = get_top_level_logger('fopd')

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

def execute_utility(args):

    logger = get_top_level_logger('fopd')

    eval_state = {'stop':True, 'sys':{'cmd':None}}
    eval_state['utils'] = {'create_private_key':create_private_key}
    eval_state['utils']['create_system'] = create_system
    eval_state['utils']['create_service_file'] = create_service_file
    eval_state['utils']['create_random_uuid'] = create_random_uuid
    eval_state['utils']['decrypt'] = decrypt_util
    eval_state['utils']['encrypt'] = encrypt_util
    eval_state['system'] = {}
    eval_state['config'] = {'device_name':'fopd'}

    # Run the repl and start with the selected utility. 
    print('utils.' + args.utility +'()')
    if args.utility == 'encrypt':
       print('input: {}'.format(args.utility_input.encode('utf-8')))
       start(eval_state, args.silent, None, start_cmd='utils.' + args.utility +'({})'.format(args.utility_input.encode('utf-8')))
    elif args.utility == 'decrypt':
       #TODO: Need to get the decrypt command working
       print('input: {}'.format(args.utility_input))
       start(eval_state, args.silent, None, start_cmd='utils.' + args.utility +'({})'.format(args.utility_input))
    else:
       start(eval_state, args.silent, None, start_cmd='utils.' + args.utility +'()')

    exit()
