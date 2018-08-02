# MVP Configuration

# This configuration file contains settings that control the operation of the mvp system.
# Nothing in the file needs to be changed from the default values in order to operate your MVP, 
# however if you wish to change the defaults or use additional features then follow the
# instructions below for the thing that you wish to change or enable.
#
# Note that there are often comments located near each setting contained in this file.
# Consult those comments for additional information.
#
# 1) device_name: Set this to something short that identifies your mvp and differentiates it. The
#                 default value is mvp.  
# 2) Light cycle.  Edit the light_controller_program value to specify the light cycle that you desire.
#                  The standard light cycle is on from 5:00 PM (local time) to 11:00 AM the next morning,
#                  and then off for 6 hours before the cycle repeats.
#
# 3) Camera picture cycle: The system defaults to taking one picture per hour at the beginning of the
#                          of the hour. The only thing that can be changed is to specify a different 
#                          minute within the hour when the picture is taken. 
#                          Edit the camera_controller_program settings to specify a different minute
#                          of the hour at which pictures should be taken.
#
# 4) Fan Controller: The fan is turned on when the max_air_temperature is exceeded and is turned off
#                    whe the temperature drops below this value.  Change the value of max_air_temperature
#                    to modify the set point for the fan.
#
# 5) Data Sample Interval: By default the system takes temperature and humidity measurements every 
#                          20 minutes. To change this edit the data_logger_sample_interval value.
#
# 6) Charting Interval: By default the web site charts for temperature and humidity are updated every
#                       30 minutes.  Edit the charting_interval value to change this.
#
# 7) MQTT data logging: By default MQTT data logging is turned off.  In order to turn it on do the
#                       following:
#                       1) enable_mqtt -> set to True
#                       2) organization_guid -> This value is sent as part of the mqtt topic.
#                       3) device_id ->  Set it to some unique value such as a guid.
#                       4) log_data_via_mqtt -> set to True
#                       5) mqtt_url and mqtt_port -> Obtain these from your mqqt broker administrator. 
#                       6) mqtt_username and "password" -> Get these from your mqtt broker administrator.
#                          You can use either plaintext or enrypted passwords (restrictions apply).
# 8) Picture uploading: The system supports posting images to a server that supports the fopd picture posting 
#                       spec (TBD: add url of the spec). Picture posting is turned off by default.
#                       In order to turn it on do the following:
#                       1) Enable posting -> Add the fop cloud service camera subscriber to the camera subscriber
#                          list.
#                       2) Specify the value for camera_device_id. Get this value from your cloud provider.
#                       3) Specify a value for the hmac_secret_key_b64_encoded. This key is used to HMAC
#                          sign the JWT claim set.
#
# organization_guid -> Required when connecting to a compatible fopd cloud provider, otherwise it is optoinal.
#                      Get this value from your cloud provider or leave it blank if not connecting to a
#                      fopd compatible cloud provider.
#
#                      - MQTT: Included in topics (e.g data/v1/[organization_guid).  
#
organization_guid = ''

# device_name -> You can give your device a custom name. The name will used at terminal prompts and other
# places where it seems useful to display the name of this device.  
#
# device_id -> device_id is required when order to connect to fopd compatible cloud provider. If you do not
#              intend to use cloud services (e.g. MQTT, image upload, etc) then you can leave this setting blank.
#              If you want to use a cloud service then get this value from your cloud provider.
#              The device id is used to uniquely identify your fopd to the world.
#
device_name = 'fopd'
device_id = ''

# ########### JWT Settings ##############
# fop_jose_id -> Audience value for JWT claim set. This value is required when using JWT to connect
#                to a fop compatible cloud provider. Required when any of the following functions are enabled:
#                   - image upload
#                Leave it blank if non of the above functions are being used.
# hmac_secret_key -> Used to sign JWT claim sets.  Required when a fop_jose_id is required.
# TBD: protect the hmac_secret_key with a local secret key.
fop_jose_id = ''
hmac_secret_key = ''

# ########### MQTT Settings #############
#    enable_mqtt -> If you are connecting to a fopd compatible MQTT Broker than set this to True,
#                   otherwise set to False.
#    mqtt_client_id -> This value is passed straight through as the client id data on the mqtt connection.
#
#    mqtt_url, mqtt_port -> Note that the MVP only supports TLS (aka SSL) communication to the MQTT broker.
#                           If your broker does not support HTTPS then it can't be used with the MVP.
#
# MQTT broker account credentials -> username and password
# The MVP client needs to know the username and password of the MQTT broker to which the client 
# should connect for sending data and receiving commands.  The password is stored here either
# as an AES encrypted string or a plain text string.
#
# TBD: Move this to the nacl libary - the same one you are using on fop for image_upload.
# Use the following command in order to encrypt the MQTT password.
# echo "put the password here" | openssl enc -e  -k "put your passphrase here" -a -aes-256-cbc
#
# Remember the passphrase and keep it secure. The mvp system will prompt you for the passphrase
# when it is started and use it to decrypt the MQTT password.
# 
# After you generate the encrypted password then modify the value for "encrypted_mqtt_password"
# to be the value that you generated.
#
# Leave the unused password field as a blank string.
# TBD: need to implement anonomous MQTT (if such a thing exists)
#
enable_mqtt = False
mqtt_client_id = device_id
mqtt_url = ''
mqtt_port = 8883
mqtt_username = ''
plain_text_mqtt_password = ''
# TBD - encrypt the pasword wiht a nacl protected secret key.
encrypted_mqtt_password = '' 

# ######## Device Ids ############
# Use the settings below to define the system composition. Once things are working then
# figure out a better way to configure systems.
#
#
#

system = {'name':'mvp',
          'device_id':''}

device_1 = {'name':'si7021',
            'instance':si7021(),
            'device_id':si7021_device_id,
            'subject_location':'chamber',
            'subject_location_id':'c0b1d0dc-66a4-46da-8aec-cc308a3359a1',
            'attributes':[{'name':'temperature', 'subject':'air', 'units': 'celsius',
                           'id':'b794687a-9970-4d12-a890-3aba98332ab8'},
                          {'name':'humidity', 'subject':'air', 'units':'percentage', 
                           'id':'3c36bae6-ec85-4898-9ab4-187dcd8c91f2'}]}

# ######## Light Controller #########
#
# Specify as many on/off times as you like.  Resolution is 1 minute so all light events
# occur on the minute.  Specify the times relative to the time zone of the system that the
# MVP is running on.
#
light_controller_program = (('on', '5:00 PM'), ('off', '11:00 AM'))
#TBD Need to enable MQTT logging.
log_light_state_vai_mqtt = False
log_light_state_to_local_couchdb = True
log_light_state_to_local_file = True


# ######## Camera Controller #########
#
# TBD: Need to add logic to the code base that skips the creation of the camera thread
# if enable_camera_controller is set to False.
# enable_camera_controller -> Set to true if you want to use a camera otherwise set to false.
#
# enable_camera_controller -> TBD
# camera_device_id -> Required for camera related fodp cloud functions. Get this from your cloud
#                     provider or leave it blank.
# camera_subscribers -> List of camera subscribers that should be notified when new pictures
#                       are taken.
#     frequency -> The current time is reduced to a string of 4 digits as HHMM with leading 
#                  zeros. Specify the regular expression that should trigger a subscriber 
#                  invocation. Once triggered the regular expression must experience a mis-match 
#                  before the subscriber will be ready to be triggered again. 
#                  e.g. r'\d\d00' -> trigger every hour at the start of the first minute of the hour.
#
enable_camera_controller = True
camera_device_id = ''
camera_subscribers = ({'sub':'LocalWebServer',  'args':{'frequency':r'\d\d00', 'take_picture_on_start':True}})
# ######## Fan Controller #########
# Speciy the target max chamber air temperature in Celsius.
# The fan will be turned on when the temperature exceeds this value.
#
max_air_temperature = 30 
fan_controller_temp_sensor = device_1['instance']


# ######## Data Logging ########
# Specify the sensor sampling interval in seconds.
#
data_logger_sample_interval = 20 * 60 
logging_devices = (device_1, )

# Specify logging of data (e.g. sensors, actuator settings etc.)
#
log_data_to_local_couchdb = True
log_data_to_local_file = False 
log_data_via_mqtt = False 


# ######## Web Charting Controller #########
# charting_interval (in minutes) sets the refresh time for the web charts.
# TBD: The chart configuration data accesses device data, so will need
# to create a compiler to create configuration files. 
#
charting_interval = 30
couchdb_location_url = 'http://127.0.0.1:5984/mvp_sensor_data/'

temp_chart = {'device':device_1,
              'attribute_index':0,
              'chart_title':'Air Temperature',
              'y_axis_title':'Degrees C',
              'x_axis_title':'Timestamp (hover over to display date)',
              'data_stream_name':'Air Temp.',
              'chart_file_name':'temp_chart.svg'}

humidity_chart = {'device':device_1,
              'attribute_index':1,
              'chart_title':'Humidity',
              'y_axis_title':'Percent',
              'x_axis_title':'Timestamp (hover over to display date)',
              'data_stream_name':'Humidity',
              'chart_file_name':'humidity_chart.svg'}

chart_list = (temp_chart, humidity_chart)
