from datetime import datetime
from logging import getLogger
from subprocess import * 
from sys import path, exc_info
import paho.mqtt.client
import paho.mqtt.client as mqtt

from config.config import enable_mqtt, encrypted_mqtt_password, mqtt_client_id, mqtt_username,\
                          mqtt_url, mqtt_port, plain_text_mqtt_password
from python.repl import get_passphrase

logger = getLogger('mvp' + '.' + __name__)

# TBD: Need to refactor to use something like pyopenssl.
def decrypt_mqtt_password(passphrase):

   # call open SSL to decrypt the encrypted MQTT password.
   # TBD - putting the passphrase on the command line may be a security issue. 
   open_ssl_decrypt_command = 'echo "' + encrypted_mqtt_password + '" | openssl enc -d -k "'\
                              + passphrase + '" -a -aes-256-cbc'
   
   try:
      #TBD - At some point upgrade to the new Python (3.5 or newer) and use the .run commmand.
      password_decrypt_results = check_output(open_ssl_decrypt_command, shell=True) 
      # print("MQTT password: " + mqtt_password + "\n") 
      #- mqtt_password = password_decrypt_results.decode("utf-8")[0:-1]
      return password_decrypt_results.decode("utf-8")[0:-1]
   except:
      logger.error('Execution of openssl failed: {}'.format(exc_info()[1]))
      return None 


def get_mqtt_password(app_state):

    if len(plain_text_mqtt_password) > 0:
        return plain_text_mqtt_password 
    elif len(encrypted_mqtt_password) > 0:
        if app_state['silent_mode']:
            #- checked
            logger.warning('The MQTT password is encrypted. There is no way to get the passphrase when'
                           + ' running in silent mode. No MQTT functions will be avaiable.')
            return None
        else: 
            return decrypt_mqtt_password(get_passphrase())
    else: 
        #- checked
        logger.warning('No MQTT password is contained in the config file. No MQTT functions will be avaiable.')
        return None

# Start the mqtt client and put a reference to it in app_state.
# If you don't start the mqtt client then don't do anything but log a message. 
#
def start(app_state, args, b):

    logger.info('starting mqtt client')

    if args['enable']:

        pw = get_mqtt_password(app_state)

        if pw is not None:
            # Note that the paho mqtt client has the ability to spawn it's own thread.
            result = start_paho_mqtt_client(pw)
            if result[0] == True:
                app_state['mqtt'] = {'client':result[1], 'organization_id':args['organization_id']}
                #- return result[1] 
            else:
                logger.error('Unable to start an MQTT client. Exiting....')
                exit()
    else:
        logger.warning('mqtt is disabled.')

    # Let the system know that you are good to go. 
    b.wait()

    #TBD: It might make sense to keep this thread alive as a "nanny" for the underlying paho thread.

# - get rid of this funcation after the start() function is tested.
#
def start_mvp_mqtt_client(app_state):

    if enable_mqtt == True:

        pw = get_mqtt_password(app_state)

        if pw is not None:
            # Note that the paho mqtt client has the ability to spawn it's own thread.
            result = start_paho_mqtt_client(pw)
            if result[0] == True:
                return result[1] 
            else:
                logger.error('Unable to start an MQTT client. Exiting....')
                exit()
        else:
            return None
    else:
        return None


mqtt_connection_results = ('connection successful', 'connection refused - incorrect protocol version',
                           'connection refused - invalid client identifier', 'connection refused - server unavailable',
                           'connection refused - bad username or password', 'connection refused - not authorised')

def connection_result(rc):
    if rc >= 0 and rc <= 5:
        return mqtt_connection_results[rc]
    else:
        return 'unknown mqtt broker  response'
    

def on_connect(client, userdata, flags, rc):

    if rc == 0:
        logger.info('mqtt broker connection successful')
    else:
        logger.error('mqtt broker connection failed: {}:{}'.format(rc, connection_result(rc)))


def on_message(client, userdata, message):
   logger.error('MQTT message received. This version of the mvp code does not support incoming MQTT messages.')

def on_publish(mqttc, obj, mid):
   logger.debug('MQTT message published, mid={}'.format(mid))

def on_disconnect(mqtt, userdata, rc):
   logger.warning('MQTT Disconnected.')

#- def on_log(client, userdata, level, buf):
#-   print('WARNING: MQTT log at {:%Y-%m-%d %H:%M:%S}:{}'.format(datetime.now(), buf))


# TBD - Need to figure out how to time it out
# after a configurable period of time.
#
def start_paho_mqtt_client(mqtt_password):

    try:
        mqtt_client = paho.mqtt.client.Client(mqtt_client_id)

        # Configure the client callback functions
        mqtt_client.on_connect = on_connect
        mqtt_client.on_message = on_message
        mqtt_client.on_publish = on_publish
        mqtt_client.on_disconnect = on_disconnect
        #- mqtt_client.on_log = on_log

        mqtt_client.enable_logger(logger)

        mqtt_client.tls_set()

        mqtt_client.username_pw_set(mqtt_username, mqtt_password)

        mqtt_client.connect(mqtt_url, mqtt_port, 60)

        # Start the MQTT client
        mqtt_client.loop_start()

        # TBD - add code here to wait for the mqtt connection to complete before proceeding.

        return [True, mqtt_client]
    except:
      logger.error('Unable to create an MQTT client: {} {}, exiting...'.format(exc_info()[0], exc_info()[1]))
      exit()
