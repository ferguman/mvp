from logging import getLogger
import re

# image subscriber
#
class CameraSubscriber():

    logger = getLogger('mvp.' + __name__)

    #- def __init__(self, frequency: 'raw string', url=None, take_picture_on_start=True) -> None:
    def __init__(self, **kwargs):

        self.regex = re.compile(kwargs.get('frequency'))
        self.posting_url = kwargs.get('url')
        self.take_picture_on_start = kwargs.get('take_picture_on_start')

        self.in_scheduled_picture_window = False

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
