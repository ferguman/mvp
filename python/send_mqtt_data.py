#- from sys import path
import datetime
from logging import getLogger

#- path.append('/opt/mvp/config')
from config.config import organization_guid

logger = getLogger('mvp.' + __name__)

def send_sensor_data_via_mqtt(device, mqtt_client, sensor_name, attribute_name, subject_name, value, units, date_time):

   # Need to find the attribute id.  Things may fail here.
   # attribute_id = list(filter(lambda attribute: attribute['name'] == attribute_name, device['attributes']))
   if 'attributes' in device:
      attribute_name_matches = [i for i in device['attributes'] if i['name'] == attribute_name]
      if len(attribute_name_matches) == 0:
         #- print('Error in send_sensor_data_via_mqtt: Attribute {0} not found in device attribute list'.format(attribute_name))
         logger.error('Error in send_sensor_data_via_mqtt: Attribute {0} not found in device attribute list'.format(\
                       attribute_name))
         return 0
      else:
         if len(attribute_name_matches) > 1:
            #- print('Error in send_sensor_data_via_mqtt: Attribute {0} found more than one in the device attribute list'.format(attribute_name))
            logger.error('Error in send_sensor_data_via_mqtt: Attribute {0}'.format(attribute_name)
                         + ' found more than onse in the device attribute list')
            return 0
   else:
      logger.error('Error in send_sensor_data_via_mqtt: Attributes list is missing from device.')
      return 0

   #If you have gotten this far then the attribute_name has been found. Now look for the attriburte id.
   #
   if 'id' in attribute_name_matches[0]:
      attribute_id = attribute_name_matches[0]['id']
   else:
      logger.error('Error in send_sensor_data_via_mqtt: Attribute id is missing.')
      return 0

   payload_value = '{"sensor":"' + device['name'] + '", '\
                    '"device_id":"'           + device['device_id'] + '", '\
                    '"subject":"'             + subject_name + '", '\
                    '"subject_location_id":"' + device['subject_location_id'] + '", '\
                    '"attribute":"'           + attribute_name + '", '\
                    '"value":"'               + value + '", '\
                    '"units":"'               + units + '", '\
                    '"time":"'                + date_time.isoformat() + '"}'

   topic =  'data/v1/' + organization_guid

   pub_response = mqtt_client.publish(topic, payload=payload_value, qos=2) 

   logger.info('published topic: {}'.format(topic))

   return 1

def send_sensor_data_via_mqtt_v2(s, mqtt):


   payload_value = '{"sensor":"'              + s['device_name'] + '", '\
                    '"device_id":"'           + s['device_id'] + '", '\
                    '"subject":"'             + s['subject'] + '", '\
                    '"subject_location_id":"' + s['subject_location_id'] + '", '\
                    '"attribute":"'           + s['attribute'] + '", '\
                    '"value":"'               + s['value'] + '", '\
                    '"units":"'               + s['units'] + '", '\
                    '"time":"'                + datetime.datetime.utcfromtimestamp(s['ts']).isoformat() + '"}'
   
   
   topic =  'data/v1/' + mqtt['organization_id']

   pub_response = mqtt['client'].publish(topic, payload=payload_value, qos=2) 

   logger.info('published topic: {}'.format(topic))

   return 1
