from logging import getLogger
from python.file_uploader import upload_camera_image

# image subscriber
#
class FopCloudStorage():

    logger = getLogger('mvp.' + __name__)

    def __init__(self, url: 'url') -> None:
        self.posting_url = url

    # upload each new image to the cloud
    def new_picture(self, file_location):
        FopCloudStorage.logger.info('uploading latest camera picture to the fop server')
        upload_camera_image(file_location, self.posting_url)
