import re

from python.logger import get_sub_logger 

# image subscriber
#
class CameraSubscriber():

    logger = get_sub_logger(__name__)

    def __init__(self, **kwargs):

        #TODO - make as many as possible of the variables below private e.g. __regix
        self.regex = re.compile(kwargs.get('frequency'))

        self.posting_url = kwargs.get('url')

        #- self.destination_dir = kwargs.get('destination_dir')

        self.take_picture_on_start = kwargs.get('take_picture_on_start')

        self.in_scheduled_picture_window = False
        self.device_id = kwargs.get('device_id')

        # Public properties
        self.name = kwargs.get('name')

    def periodic_call(self):
        """ The camera_controller will call this variable once per cycle from within it's control loop.
            Typcially control loops run every second.  Override this method if you need this class to be
            called periodically. For example if you are implementing a network transaction and need to be
            able to do retries """

        pass

    def wants_picture(self, time_stamp, startup_flag):
        """ If the configuration regex gets a hit on the current hours and minutes and
            the previous regex match failed then return true otherwise return false.
            In other words only fire on a transition from the regex failing to the regex
            passing.
        """

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
