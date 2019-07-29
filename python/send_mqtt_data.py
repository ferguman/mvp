# This module is not thread safe. Don't call functions in it from multiple threads.  The idea is that one
# MQTT thread will call the functions in this module and that thread will be responsible for synchronizing all
# MQTT requests from all the different threads.

from sys import path
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
   
   topic =  'data/v1/' + organization_id

   pub_response = mqtt_client.publish(topic, payload=payload_value, qos=2) 

   logger.info('published topic: {}'.format(topic))

def make_sensor_reading_payload(sr):

    return  '{"sensor":"'             + sr['device_name'] + '", '\
            '"device_id":"'           + sr['device_id'] + '", '\
            '"subject":"'             + sr['subject'] + '", '\
            '"subject_location_id":"' + sr['subject_location_id'] + '", '\
            '"attribute":"'           + sr['attribute'] + '", '\
            '"value":"'               + sr['value'] + '", '\
            '"units":"'               + sr['units'] + '", '\
            '"time":"'                + datetime.datetime.utcfromtimestamp(sr['ts']).isoformat() + '"}'

def publish_mqtt_topic(mqtt_client, topic, payload_value):

   result = mqtt_client.publish(topic, payload=payload_value, qos=2)
   logger.info('published topic: {}'.format(topic))
   return result

def publish_sensor_reading(mqtt_client, org_id, sensor_reading):

    publish_mqtt_topic(mqtt_client, 'data/v1/' + org_id, make_sensor_reading_payload(sensor_reading))

def publish_cmd_response(mqtt_client, org_id, response):

    publish_mqtt_topic(mqtt_client, 'cr/v1/' + org_id, response)
