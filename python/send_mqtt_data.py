# This module is not thread safe. Don't call functions in it from multiple threads.  The idea is that one
# MQTT thread will call the functions in this module and that thread will be responsible for synchronizing all
# MQTT requests from all the different threads.

from sys import path, exc_info
import datetime
from python.logger import get_sub_logger 
from logging import getLogger

path.append('/opt/mvp/config')
from config import organization_guid

logger = getLogger('mvp.' + __name__)
logger = get_sub_logger(__name__)

def send_sensor_data_via_mqtt_v2(s, mqtt_client, organization_id):

   payload_value = '{"sensor":"'              + s['device_name'] + '", '\
                    '"device_id":"'           + s['device_id'] + '", '\
                    '"subject":"'             + s['subject'] + '", '\
                    '"subject_location_id":"' + s['subject_location_id'] + '", '\
                    '"attribute":"'           + s['attribute'] + '", '\
                    '"value":"'               + s['value'] + '", '\
                    '"units":"'               + s['units'] + '", '\
                    '"time":"'                + datetime.datetime.utcfromtimestamp(s['ts']).isoformat() + '"}'
  
   # TODO Mosuqitto broker allows configuraton of an ACL list that controls topic 
   # publication.  One can specify an ACL line of the form: pattern write
   #      data/v2/%c where %c is a pattern that matches the client ID of the mqtt
   #      conection.  This will allow the imposotion of the rule that fopd clients   #      can only publish write /data/v2/[client_id] topics and the broker will
   #      will ignore all other published topics. Need to test this stuff and then   #      implement /data/v2/[client_id] publishing here.
   topic =  'data/v1/' + organization_id

   pub_response = mqtt_client.publish(topic, payload=payload_value, qos=2) 

   logger.info('published topic: {}'.format(topic))

def make_sensor_reading_payload(sr):

    try:
        units = 'None'
        if sr['units']:
            units = sr['units']

        return  '{"sensor":"'             + sr['device_name'] + '", '\
                '"device_id":"'           + sr['device_id'] + '", '\
                '"subject":"'             + sr['subject'] + '", '\
                '"subject_location_id":"' + sr['subject_location_id'] + '", '\
                '"attribute":"'           + sr['attribute'] + '", '\
                '"value":"'               + sr['value'] + '", '\
                '"units":"'               + units + '", '\
                '"time":"'                + datetime.datetime.utcfromtimestamp(sr['ts']).isoformat() + '"}'
    except:
        logger.error('exception occurred creating mqtt topic for sensor reading: {}, error: {}{}'.format(\
                      sr, exc_info()[0], exc_info()[1]))

def publish_mqtt_topic(mqtt_client, topic, payload_value):

   result = mqtt_client.publish(topic, payload=payload_value, qos=2)
   logger.info('published topic: {}'.format(topic))
   return result

def publish_sensor_reading(mqtt_client, org_id, sensor_reading):

    publish_mqtt_topic(mqtt_client, 'data/v1/' + org_id, make_sensor_reading_payload(sensor_reading))

def publish_cmd_response(mqtt_client, org_id, response):

    # TODO: Need to implement /cr/v2/[client_id] publishing. See note about ACLs
    #       elsewhere in this file.
    publish_mqtt_topic(mqtt_client, 'cr/v1/' + org_id, response)
