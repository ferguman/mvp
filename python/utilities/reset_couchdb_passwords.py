#- import fileinput
#- import re
from json import dumps
from os import path
from subprocess import run 
from sys import exc_info
from time import sleep
import requests

from python.encryption.nacl_fop import encrypt
from python.logger import get_sub_logger 
from python.data_file_paths import couchdb_local_config_file_directory, configuration_directory_location
from python.random_password import generate_password
from python.file_utils import change_file_line

logger = get_sub_logger(__name__)

def reset_couchdb_passwords(args):

    try:    

        # write the password to the couchdb configuration file
        logger.info('changing couchdb password in local.ini. Reset the couchdb service to take up the new password.')
        # Note: The couchdb service updates the local.ini file to contain the hashed password instead of the plaintext
        #       password. So the admin password is essentially unknown.  
        couchdb_pwd = generate_password(16)
        pwd_changed = change_file_line(path.join(couchdb_local_config_file_directory, 'local.ini'),
                                                 r'^admin[ |\t]*=', 'admin = {}\n'.format(couchdb_pwd))
        
        if not pwd_changed:
            logger.error('Unable to reset the couchdb admin password.')
            raise Exception('ERROR: unable to reset couchdb admin password.')
        else:
            logger.info('Writing the couchdb admin password to the config file.')
            change_file_line(path.join(configuration_directory_location, 'config.py'), 
                             r'^couchdb_admin_password_b64_cipher[ |\t]*=', 
                             'couchdb_admin_password_b64_cipher = {}\n'.format(encrypt(couchdb_pwd.encode('utf-8'))))

            logger.info('Restarting couchdb so that the admin password change is taken up.')
            run('sudo systemctl restart couchdb', shell=True)
            
        # get a random value for the fopd couchdb user password
        fopd_password = generate_password(16)
        #- logger.info('password: {}'.format(fopd_password))

        logger.info('waiting 5 seconds for couchdb to start, so that I can query it')
        sleep(5)

        # Get the document for the fopd user.
        # Note: Use the admin credentials created above; you can't use the new value in the config.py
        #       file because it is not loaded into the Python interpretter.
        logger.info('retrieving document for fopd user from couchdb')
        r = requests.get("http://127.0.0.1:5984/_users/org.couchdb.user:fopd", 
                         auth=('admin', couchdb_pwd))
        if r.status_code == 200:
            logger.info('resetting fopd couchdb password')
            new_fopd_pwd = generate_password(16)
           
            #+ """ DEBUG
            print('admin password {}'.format(couchdb_pwd))
            print('fopd password {}'.format(new_fopd_pwd))
            #+ """

            # The couchdb API is a JSON driven website. POST to this API a request
            # to change the password for the fopd user.
            r = requests.put('http://localhost:5984/_users/org.couchdb.user:fopd', 
                             data = dumps({'name':'fopd', 'roles':[], 'type':'user', 'password':'{}'.format(new_fopd_pwd)}),
                             auth=('admin', couchdb_pwd),
                             headers = {'Accept':'application/json', 'Content-Type':'application/json',
                                        'If-Match':'{}'.format(r.json()['_rev'])})
            if r.status_code == 201:
                logger.info('updating the configuration file with the new fopd couchdb password')
                change_file_line(path.join(configuration_directory_location, 'config.py'), 
                             r'^couchdb_password_b64_cipher[ |\t]*=', 
                             'couchdb_password_b64_cipher = {}\n'.format(encrypt(new_fopd_pwd.encode('utf-8'))))
            else:
                logger.error('Cannot reset the database. Couch reply {}:{}'.format(r.status_code, r.json()))
        else:
            logger.error('Unable to retrieve user document for fopd from the couchdb database')
            raise Exception('ERROR Unable to retrieve user document for fopd from the couchdb database')

        return True if args['silent'] else 'OK'

    except:
        logger.error('Exception in reset_couchdb_passwords: {}, {}'.format(exc_info()[0], exc_info()[1]))
        return False if args['silent'] else 'ERROR'

