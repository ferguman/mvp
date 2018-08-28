from datetime import datetime
from logging import getLogger
from queue import Queue, Empty
from subprocess import * 
from sys import path, exc_info
from time import sleep
import paho.mqtt.client
import paho.mqtt.client as mqtt

from config.config import enable_mqtt, encrypted_mqtt_password, mqtt_client_id, mqtt_username,\
                          mqtt_url, mqtt_port, plain_text_mqtt_password
from python.repl import get_passphrase
from python.send_mqtt_data import send_sensor_data_via_mqtt_v2

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

        return [True, mqtt_client]
    except:
      logger.error('Unable to create an MQTT client: {} {}, exiting...'.format(exc_info()[0], exc_info()[1]))
      exit()

def make_mqtt_help(res_name):

    def mqtt_help():
        return """\
        {0}.publish(sensor_reading) - Publish a sensor reading..
        """.format(res_name)

    return mqtt_help

# Start the mqtt client and put a reference to it in app_state.
# If you don't start the mqtt client then don't do anything but log a message. 
#
def start(app_state, args, b):

    logger.info('starting mqtt client')
    
    publish_queue = Queue()
    mqtt_client = None

    app_state[args['name']] = {}

    if args['enable']:

        pw = get_mqtt_password(app_state)

        if pw is not None:
            # Note that the paho mqtt client has the ability to spawn it's own thread.
            result = start_paho_mqtt_client(pw)
            if result[0] == True:
                app_state[args['name']]['publish_queue'] = publish_queue
                mqtt_client = result[1]
            else:
                logger.error('Unable to start an MQTT client. Exiting....')
                exit()

        app_state[args['name']]['help'] = make_mqtt_help(args['name'])

        # Let the system know that you are good to go. 
        b.wait()

        while not app_state['stop']:

            """
            Queue.get(block=True, timeout=None)
                Remove and return an item from the queue. If optional args block is true and timeout is None (the default), 
                block if necessary until an item is available. If timeout is a positive number, it blocks at most timeout 
                seconds and raises the Empty exception if no item was available within that time. Otherwise (block is false),
                return an item if one is immediately available, else raise the Empty exception (timeout is ignored in that
                case).
            """
            try:
                r = publish_queue.get(False)
                logger.info('publishing reading via mqtt')
                send_sensor_data_via_mqtt_v2(r, mqtt_client, args['organization_id'])
                
                # Bypass the sleep command in order to keep draining the queue in real time.
                continue
            except Empty:
                # this is ok. It just means the publish queue is empty.
                pass
            
            sleep(1)

        logger.info('mqtt client interface thread stopping.')

    else:
        logger.warning('mqtt is disabled.')

