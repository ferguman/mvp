from os import path, getcwd
from uuid import uuid4

from jinja2 import Environment, FileSystemLoader

from python.encryption.nacl_fop import encrypt
from python.utilities.prompt import prompt

from python.data_file_paths import configuration_directory_location

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

    vals = ('fop_jose_id', 'hmac_secret_key_b64_cipher', 'fws_url')
    prompts = {'fop_jose_id':'Enter the JWT id of the fop that you wish to connect to\n'+\
                             '(e.g. c0e94b7e-2ab9-45c7-9dfb-468f349c67a2)',
               'hmac_secret_key_b64_cipher':'Enter the value of your jose fop hmac secret key.\n'+\
                                            'This is a 32 character URL safe random token provided by your fop provider.',
               'fws_url':'Enter the URL of your fopd web services server.'
              } 
    generators = {'hmac_secret_key_b64_cipher': {'default':lambda s: encrypt(bytes(s, 'utf-8'))}}

    #- if sys_type == 'fc1':
    #-     vals = vals + ('fws_url',)
    #-    prompts['fws_url'] = 'Enter the URL of your Farm Web Services server.\n'
        
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
    generators = {'mqtt_password_b64_cipher':{'default':lambda s: encrypt(bytes(s, 'utf-8'))},
                  'mqtt_port':{'default':lambda s: int(s)}}
    return prompt(vals, prompts, generators)


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
          'exit     -> to exit this utility.',
          '\n\n',
          'Note: If you have an existing configuration file then exit this utility and\n',
          'copy your existing configuration file to:',
          '{}config.py.\n'.format(configuration_directory_location),
          'Once your configuraiton file is in place you can run the fopd system.')



    cmd = input('fopd: ')

    if cmd.lower() == 'exit':
        return 'CANCELLED'

    if cmd.lower() == 'fc1':
        template_file = '/templates/config_fc1.j2' 
    elif cmd.lower() == 'fc2':
        template_file = 'config_fc2.j2' 
    elif cmd.lower() == 'mvp':
        template_file = 'config_mvp.j2' 
    elif cmd.lower() == 'custom':
        template_file = '/templates/config_custom.j2'
    elif cmd.lower() == 'download':
        print('The download function is not available in this version of the fopd client.')
        return 'CANCELLED'
    else:
        print('ERROR - unknown hardware type')


    config = {'identity':get_identity(cmd.lower()),
              'jwt':get_jwt_info(cmd.lower()), 
              'couchdb':get_couchdb_info(cmd.lower()),
              'mqtt':get_mqtt_info(cmd.lower())
             }

    # generate the config file
    #- tp = path.join(getcwd(), 'config')
    #- cfp = path.join(tp, 'config.py')
    cfp = path.join(configuration_directory_location, 'config.py')
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

    print('Your configuration file has been written to {} replacing any existing file.\n'.format(cfp),
          'You can edit the configuration file by hand to change any settings.  Be sure to restart\n',
          'the fopd system after you save your edits.')
    
    return 'OK'
