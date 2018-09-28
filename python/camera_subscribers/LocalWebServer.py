from os import getcwd
from python.camera_subscribers.CameraSubscriber import CameraSubscriber
from shutil import copyfile
from sys import exc_info

# Copy the picture to the web directory
#
class LocalWebServer(CameraSubscriber):

    def new_picture(self, file_location):
       try:
          current_image_copy_location = getcwd() + self.destination_dir + 'image.jpg'
          CameraSubscriber.logger.info('updating local web site picture')
          CameraSubscriber.logger.debug('copying newest picture to web directory: source image'
                                      + ' path: {}, destination path: {}'.format(\
                                        file_location, current_image_copy_location))
          copyfile(file_location, current_image_copy_location)
       except:
          CameraSubscriber.logger.error('Coudn not copy latest image file to the web directory.'
                                      + ' Check fswebcam for proper operations: {}, {}'.format(\
                                          exc_info()[0], exc_info()[1]))
