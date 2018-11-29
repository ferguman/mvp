import threading
from os import path, getcwd, mkdir
from uuid import uuid4

from jinja2 import Environment, FileSystemLoader, select_autoescape

from python.logger import get_top_level_logger
from python.repl import start
from python.encryption.nacl_utils import create_random_key
from python.encryption.nacl_fop import encrypt

logger = get_top_level_logger('fopd')

def create_config_directory() -> 'path_to_config_file':

    cp = path.join(getcwd(), 'config')
    if not path.isdir(cp):
        print('Creating directory named config at {}'.format(cp))
        mkdir(cp)

    return cp

def get_identity(sys_type: str) -> dict:

    # ask for the identity settings
    vals = ('device_name', 'device_id', 'organization_guid')
    prompts =  {'device_name':'Enter a short name for device (e.g. fc1 or basil_bomba)',
                'device_id':'Enter your device guid (e.g. c0e94b7e-2ab9-45c7-9dfb-468f349c67a2)\n'+\
                            'Enter auto if you wish the system to autogenerate one for you.', 
                'organization_guid':'Enter your organizaiton guid (e.g. c0e94b7e-2ab9-45c7-9dfb-468f349c67a2)\n'+\
                                    'Enter auto if you wish the system to autogenerate one for you.'
               }
    generators = {'device_id':{'auto':lambda s: uuid4()},'organization_guid':{'auto':lambda s: uuid4()}}

    if sys_type == 'fc1':
       vals = vals + ('arduino_id', 'camera_guid')
       prompts['arduino_id'] = 'Enter your arduino guid.  Enter auto if you wish the system\n'+\
                               'to generate an id for you.'
       prompts['camera_guid'] = 'Enter the guid of your food computers camera.  Enter auto if you wish the\n'+\
                                'system to generate a guid for you.'
       generators['arduino_id'] = {'auto':lambda s: uuid4()}
       generators['camera_guid'] = {'auto':lambda s: uuid4()}

    return prompt(vals, prompts, generators)

def get_jwt_info(sys_type: str) -> dict:

    vals = ('fop_jose_id', 'hmac_secret_key_b64_cipher')
    prompts = {'fop_jose_id':'Enter the JWT id of the fop that you wish to connect to\n'+\
                             '(e.g. c0e94b7e-2ab9-45c7-9dfb-468f349c67a2)',
               'hmac_secret_key_b64_cipher':'Enter the value of your jose fop hmac secret key.\n'+\
                                            'This is a 32 character URL safe random token provided by your fop provider.'} 
    generators = {'hmac_secret_key_b64_cipher': {'default':lambda s: encrypt(bytes(s, 'utf-8'))}}

    if sys_type == 'fc1':
        vals = vals + ('fws_url',)
        prompts['fws_url'] = 'Enter the URL of your Farm Web Services server.\n'
        
    return prompt(vals, prompts, generators)

def get_couchdb_info(sys_type:str) -> dict:

    vals = ('local_couchdb_url', 'couchdb_username_b64_cipher', 'couchdb_password_b64_cipher')
    prompts = {'local_couchdb_url':'Enter the URL of your local couchdb server:',
               'couchdb_username_b64_cipher':'Enter the couchdb username:',
               'couchdb_password_b64_cipher':'Enter the couchdb password:'}
    generators = {'couchdb_username_b64_cipher':{'default':lambda s: encrypt(bytes(s, 'utf-8'))},
                  'couchdb_password_b64_cipher':{'default':lambda s: encrypt(bytes(s, 'utf-8'))}}
    return prompt(vals, prompts, generators)

def get_mqtt_info(sys_type:str) -> dict:
    vals = ('mqtt_username', 'mqtt_password_b64_cipher', 'mqtt_url', 'mqtt_port')
    prompts = {'mqtt_username':'Enter your MQTT broker account username.', 
               'mqtt_password_b64_cipher':'Enter your MQTT account password.',
               'mqtt_url':'Enter your MQTT broker url.',
               'mqtt_port':'Enter your MQTT broker port number.'}
    generators = {'mqtt_password_b64_cipher':{'default':lambda s: encrypt(bytes(s, 'utf-8'))}}
    return prompt(vals, prompts, generators)

def prompt(vals:tuple, prompts:dict, generators:dict):

    result = {}
    
    for val in vals:
        print(prompts[val])
        cmd = input('fopd: ')

        if val in generators:
            # look for invocation of custom generators by user (e.g. they entered 'auto')
            if cmd.lower() in generators[val]:
                result[val] = generators[val][cmd.lower()](cmd.lower())
            # look for a default value generator
            elif 'default' in generators[val]: 
                result[val] = generators[val]['default'](cmd)
            else:
                result[val] = cmd
        else:
            result[val] = cmd

    return result 


def create_system():
    """ Ask the user what hardware their software will be run on and
        then create the required configuration file. """

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

    if cmd.lower() == 'exit':
        return 'CANCELLED'

    if cmd.lower() == 'fc1':
        template_file = 'config_fc1.j2' 
    elif cmd.lower() == 'fc2':
        template_file = 'config_fc2.j2' 
    elif cmd.lower() == 'mvp':
        template_file = 'config_mvp.j2' 
    elif cmd.lower() == 'custom':
        template_file = 'config_custom.j2'
    elif cmd.lower() == 'download':
        print('The download function is not availble in this version of the fopd client.')
        return 'CANCELLED'
    else:
        print('ERROR - unknown hardware type')

    config = {'identity':get_identity(cmd.lower()),
              'jwt':get_jwt_info(cmd.lower()), 
              'couchdb':get_couchdb_info(cmd.lower()),
              'mqtt':get_mqtt_info(cmd.lower())
             }

    # generate the config file
    tp = path.join(getcwd(), 'config')
    cfp = path.join(tp, 'config.py')
    if path.isfile(cfp):
        print('WARNING: A configuration file already exists: {}.\n'.format(cfp),
              'If you proceed this file will be deleted. Any configuration in this file will be lost.\n',
              'Enter yes to proceed, no to exit')
        cmd = input('fopd: ')

        if cmd.lower() != 'yes':
            return 'CANCELED'

    # Create a jinja2 environment and compile the template 
    env = Environment(
       loader=FileSystemLoader(tp),
       trim_blocks=True
       ) 
    template = env.get_template(template_file)

    # Render the jinja2 template into a new version of the config file
    with open(cfp, 'w') as f:
        f.write(template.render(config=config))

    print('Your configuration file has been written to {} replacing any existing file.'.format(cfp))
    print('You can edit the configuration file by hand to change any settings.  Be sure to restart\n'+\
          'the fopd system after you save your edits.')
    
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

    # app_state[args['name']]['snap'] = lambda: snap(app_state['sys']['cmd'], args['pose_on_cmd'], args['pose_off_cmd'])
    
    eval_state = {'stop':True, 'sys':{'cmd':None}}
    eval_state['utils'] = {'create_private_key':create_private_key}
    eval_state['utils']['create_system'] = create_system
    eval_state['system'] = {}
    eval_state['config'] = {'device_name':'fopd'}

    # Run the repl and start with the selected utility. 
    start(eval_state, args.silent, start_cmd='utils.'+ args.utility +'()')

    exit()
