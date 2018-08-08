from python.camera_subscribers.CameraSubscriber import CameraSubscriber
from python.file_uploader import upload_camera_image

# image subscriber
#
class FopCloudStorage(CameraSubscriber):

    
    # upload each new image to the cloud
    def new_picture(self, file_location):
        CameraSubscriber.logger.info('uploading latest camera picture to the fop server')
        upload_camera_image(file_location, self.posting_url, self.device_id)
