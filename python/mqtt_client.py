# Note: PJON is an open source network protocol for IoT communication that could be
#       an alternative for MQTT. See https://github.com/gioblu/PJON

from datetime import datetime
from queue import Queue, Empty
from subprocess import * 
from sys import path, exc_info
from time import sleep, time

#- import paho.mqtt.client
import paho.mqtt.client as mqtt

from python.logger import get_sub_logger 
from python.encryption.nacl_fop import decrypt
from python.send_mqtt_data import publish_sensor_reading, publish_cmd_response #- send_sensor_data_via_mqtt_v2

logger = get_sub_logger(__name__)

mqtt_connection_results = ('connection successful', 'connection refused - incorrect protocol version',
                           'connection refused - invalid client identifier', 'connection refused - server unavailable',
                           'connection refused - bad username or password', 'connection refused - not authorised')

connection_rc = None
connection_flags = None

def connection_result(rc):
    if rc >= 0 and rc <= 5:
        return mqtt_connection_results[rc]
    else:
        return 'unknown MQTT broker  response'

def make_mqtt_status_cmd():

    global connection_rc, connection_flags

    def mqtt_status():
        return('connection code: {}, connection_flags: {}'.format(rc_text(connection_rc), connection_flags))

    return mqtt_status
    

def rc_text(rc):

    if rc:

        rc_text = {0:'Connection successful', 1:'Connection refused - incorrect protocol version',
                   2:'Connection refused - invalid client identifier', 3:'Connection refused - server unavailable',
                   4:'Connection refused - bad username or password', 5:'Connection refused - not authorised'}

        if rc >= 0 and rc <= 5:
            return rc_text[rc]
        else:
            return 'unknown connection result code: {}'.format(rc)
    else:
       return None 


def make_mqtt_help(res_name):

    def mqtt_help():
        return """\
        {0}.publish(sensor_reading) - Publish a sensor reading.
        """.format(res_name)

    return mqtt_help


def make_on_connect(mqtt_client_id):

    def on_connect(client, userdata, flags, rc):

        global connection_rc, connection_flags
        connection_rc = rc
        connection_flags = flags

        if rc == 0:
            logger.info('MQTT broker connection successful. Clean session: {}'.format(flags['session present']))
            if flags['session present'] != 1:
                # The broker doesn't have the previous session so you need to subscribe again
                subscribe_for_commands(client, mqtt_client_id)
        else:
            logger.error('MQTT broker connection failed: {}:{}'.format(rc, connection_result(rc)))

    return on_connect

"""-
def on_connect(client, userdata, flags, rc):

    global connection_rc, connection_flags
    connection_rc = rc
    connection_flags = flags

    if rc == 0:
        logger.info('MQTT broker connection successful. Clean session: {}'.format(flags['session present']))
        if flags['session present'] != 1:
            # The broker doesn't have the previous session so you need to subscribe again
            subscribe_for_commands(client, mqtt_client_id)
    else:
        logger.error('MQTT broker connection failed: {}:{}'.format(rc, connection_result(rc)))
"""

def on_disconnect(mqtt, userdata, rc):

    global connection_rc
    connection_rc = rc
    
    logger.warning('MQTT Disconnected.')


def on_publish(mqttc, obj, mid):

   logger.debug('MQTT message published, mid={}'.format(mid))


def on_subscribe(mqtt, userdata, mid, granted_qos):

    logger.info("subscribed, data: {}, mid: {}".format(userdata, mid))


def make_on_message(app_state, publish_queue):

    # message -> an instance of MWTTMessage. This is a class with members topic, payload, qos,
    #            and retain.
    def on_message(client, userdata, message):
        
        logger.info('MQTT command received: userdata: {}, payload: {}'.format(userdata, message.payload.decode('utf-8')))

        # execute the command
        # TODO: Need to add a signature to commands so that the fopd can confirm that the 
        #       command was issued by the fop cloud.
        publish_queue.put(['cmd_response', app_state['sys']['cmd'](message.payload.decode('utf-8'))])

    return on_message


# TBD - Need to figure out how to time it out
# after a configurable period of time.
#
def start_paho_mqtt_client(args, app_state, publish_queue):

    # TODO - investigate how to tell the broker to keep sessions alive between disconnections.
    #        This may be help or maybe not.
    try:
        mqtt_client = mqtt.Client(args['mqtt_client_id'])

        # Configure the client callback functions
        #- mqtt_client.on_connect = on_connect
        mqtt_client.on_connect = make_on_connect(args['mqtt_client_id'])
        mqtt_client.on_message = make_on_message(app_state, publish_queue)
        mqtt_client.on_publish = on_publish
        mqtt_client.on_disconnect = on_disconnect
        mqtt_client.on_subscribe = on_subscribe

        mqtt_client.enable_logger(logger)

        mqtt_client.tls_set()

        # TODO: This software is currently embedded in the fopd codebase. fopd is intended to be run as an
        # locally unattended service so a client certificate should be used here, not a username, password pair.
        #
        mqtt_client.username_pw_set(args['mqtt_username'], decrypt(args['mqtt_password_b64_cipher']))

        mqtt_client.connect(args['mqtt_url'], args['mqtt_port'], 60)

        # Start the MQTT client - loop_start causes the mqtt_client to spawn a backround thread which
        #                         handles the mqtt communications.  The loop_start call thus
        #                         returns control to this thread immediately.
        mqtt_client.loop_start()

        return mqtt_client
    except:
      logger.error('Unable to create an MQTT client: {} {}, exiting...'.format(exc_info()[0], exc_info()[1]))
      return None

#- def subscribe_for_commands(mqtt_client, device_id):
def subscribe_for_commands(mqtt_client, mqtt_client_id):

    # TODO - Design substriction system and then complete it.
    # Subscribe to the broker so commands can be received.
    # QOS 2 = Exactly Once
    try:
       topic = 'cmd/' + mqtt_client_id
       result = mqtt_client.subscribe(topic, 2)
       if result[0] == 0:
           logger.info('MQTT subscription to topic {} requested'.format(topic))
           # TBD: need to research what the following command does.
           # mqtt_client.topic_ack.append([topic_list, result[1],0])
       else:
           logger.error('MQTT subcription (topic: {}) request failed'.format('cmd/' + mqtt_client_id))
    except Exception as e:
        logger.error('Exception occurred while attempting to subscribe to MQTT: {}{}'.format(\
                     exc_info()[0], exc_info()[1]))
"""
2020-10-04 03:15:04 AM CDT WARNING p3demo.python.mqtt_client:MQTT Disconnected.
2020-10-04 03:15:06 AM CDT INFO p3demo.python.mqtt_client:mqtt broker connection successful
"""

# Start the mqtt client and put a reference to it in app_state.
# If you don't start the mqtt client then don't do anything but log a message. 
def start(app_state, args, b):

    logger.setLevel(args['log_level'])
    logger.info('starting MQTT client')
    
    app_state[args['name']] = {}

    publish_queue = Queue()
    app_state[args['name']]['publish_queue'] = publish_queue
    app_state[args['name']]['help'] = make_mqtt_help(args['name'])
    app_state[args['name']]['status'] = make_mqtt_status_cmd()

    mqtt_client = None

    if args['enable']:

        last_client_start_attempt_time = time()
        # TODO app_state is too much to give here. figure out what the 
        # the function needs and only give that.
        # Note that the paho mqtt client has the ability to spawn it's own thead.
        mqtt_client = start_paho_mqtt_client(args, app_state, publish_queue)

        """ - Move subscription into the on_connect event.
        if mqtt_client: 
            subscribe_for_commands(mqtt_client, args['mqtt_client_id'])
        """

        # Let the system know that you are good to go.
        try:
            b.wait()
        except Exception as err:
            # assume a broken barrier
            logger.error('barrier error: {}'.format(str(err)))
            app_state['stop'] = True

        while not app_state['stop']:

            if mqtt_client:

                """
                Queue.get(block=True, timeout=None)
                    Remove and return an item from the queue. If optional args block is true and timeout is None (the default), 
                    block if necessary until an item is available. If timeout is a positive number, it blocks at most timeout 
                    seconds and raises the Empty exception if no item was available within that time. Otherwise (block is false),
                    return an item if one is immediately available, else raise the Empty exception (timeout is ignored in that
                    case).
                """
                try:
                    item = publish_queue.get(False)

                    try:

                        if not mqtt_client: 
                            logger.error('there is no MQTT client available for published request: {}'.format(item[0]))
                            continue

                        if item[0] == 'sensor_reading':
                            logger.info('publishing reading via MQTT')
                            publish_sensor_reading(mqtt_client, args['organization_id'], item[1])

                            # Bypass the sleep command in order to keep draining the queue in real time.
                            continue

                        if item[0] == 'cmd_response': 
                            logger.info('publishing commmand response via MQTT')
                            publish_cmd_response(mqtt_client, args['organization_id'], item[1]) 

                            # Bypass the sleep command in order to keep draining the queue in real time.
                            continue
                       
                        else:
                            logger.error('unknown MQTT publish item encountered: {}'.format(item[0]))

                    except Exception as e:
                        logger.error('exception occurred in main loop of MQTT thread: {}{}'.format(\
                                     exc_info()[0], exc_info()[1]))
               
                except Empty:
                    # This is ok. It just means the publish queue is empty.
                    pass
            else:
                # attempt to create a client if we don't have one but don't do it every second
                if  time() - last_client_start_attempt_time >= args['client_create_retry_interval']: 
                    last_client_start_attempt_time = time()
                    mqtt_client = start_paho_mqtt_client(args, app_state, publish_queue)
                    
                    if mqtt_client: 
                        subscribe_for_commands(mqtt_client, args['mqtt_client_id'])

            
            sleep(1)

        logger.info('MQTT client interface thread stopping.')

    else:
        logger.warning('MQTT is disabled.')
