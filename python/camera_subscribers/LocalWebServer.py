from logging import getLogger
from os import getcwd
from shutil import copyfile
from sys import exc_info

# Copy the picture to the web directory
#
class LocalWebServer():

    logger = getLogger('mvp.'  + __name__)

    def new_picture(self, file_location):

       try:
          current_image_copy_location = getcwd() + '/web/image.jpg'
          LocalWebServer.logger.info('updating local web site picture')
          LocalWebServer.logger.debug('copying newest picture to web directory: source image'
                                    + ' path: {}, destination path: {}'.format(\
                                    file_location, current_image_copy_location))
          copyfile(file_location, current_image_copy_location)
       except:
          LocalWebServer.logger.error("Coudn't copy latest image file to the web directory."
                                      + ' Check fswebcam for proper operations: {}, {}'.format(\
                                      exc_info()[0], exc_info()[1]))

