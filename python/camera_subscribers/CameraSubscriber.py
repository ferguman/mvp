import re

from python.logger import get_sub_logger 

# image subscriber
#
class CameraSubscriber():

    logger = get_sub_logger(__name__)

    def __init__(self, **kwargs):

        self.regex = re.compile(kwargs.get('frequency'))

        self.posting_url = kwargs.get('url')
        self.destination_dir = kwargs.get('destination_dir')

        self.take_picture_on_start = kwargs.get('take_picture_on_start')

        self.in_scheduled_picture_window = False
        self.device_id = kwargs.get('device_id')

    def wants_picture(self, time_stamp, startup_flag):

        if startup_flag and self.take_picture_on_start:
            return True
        
        if self.regex.match(str(time_stamp.hour * 100 + time_stamp.minute).zfill(4)) != None:
            if not self.in_scheduled_picture_window:
                self.in_scheduled_picture_window = True
                return True
            else:
                return False
        else:
            self.in_scheduled_picture_window = False
            return False
