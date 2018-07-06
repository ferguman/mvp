from base64 import standard_b64decode, standard_b64encode
from config.config import device_id, camera_device_id, hmac_secret_key_b64_encoded, image_post_url
from hashlib import sha256
from jose import jwt
from requests import post
from time import time
from uuid import uuid4

# Make the JWT claim set
def claim_info(file_hash):
    
    issue_time = int(time())

    return {'iss':device_id,
            'exp':issue_time + 60,
            'sub':camera_device_id,
            'nbf':issue_time - 60,
            'iat':issue_time,
            'jti':str(uuid4()),
            'fh':file_hash}

def get_file_hash(path_name):

    m = sha256()
    with open(path_name, 'rb') as f:
        for line in f:
            m.update(line)
            
    #return 'bogus hash'
    return standard_b64encode(m.digest()).decode('utf-8')

def get_jws_url(path_name):

    return jwt.encode(claim_info(get_file_hash(path_name)), 
                      standard_b64decode(hmac_secret_key_b64_encoded),
                      algorithm='HS256')

def upload_camera_file(path_name):

    with open(path_name, 'rb') as f:
        r = post('{}?s={}'.format(image_post_url, get_jws_url(path_name)), files={'image.jpg':f}) 

    return r
