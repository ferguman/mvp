from os import getcwd, path
from python.camera_subscribers.CameraSubscriber import CameraSubscriber
from shutil import copyfile
from sys import exc_info

from python.data_file_paths import local_web_image_directory

# Copy the picture to the web directory
#
class LocalWebServer(CameraSubscriber):

    def new_picture(self, file_location):

       try:
          current_image_copy_location = path.join(local_web_image_directory,  'image.jpg')
          CameraSubscriber.logger.info('updating local web site picture')
          CameraSubscriber.logger.debug('copying newest picture to web directory: source image'
                                      + ' path: {}, destination path: {}'.format(\
                                        file_location, current_image_copy_location))
          copyfile(file_location, current_image_copy_location)
       except:
          CameraSubscriber.logger.error('Could not copy latest image file to the web directory ({}).'.format(local_web_image_directory)
                                      + ' Check fswebcam for proper operations: {}, {}'.format(\
                                          exc_info()[0], exc_info()[1]))
