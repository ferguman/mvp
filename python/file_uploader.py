from base64 import standard_b64decode, standard_b64encode
from config.config import device_id, camera_device_id, hmac_secret_key, image_post_url, fop_jose_id
from datetime import datetime
from hashlib import sha256
from jose import jws 
from requests import post
from time import time
from uuid import uuid4

# Note: This module uses JWT security (via jose).  Paseto is another system for implemeting token based security.

def extract_timestamp(path_name) -> 'timestamp':

    dt = path_name.split("/")[-1].split(".")[0]

    return datetime(int(dt[0:4]), int(dt[4:6]), int(dt[6:8]), hour=int(dt[9:11]), minute=int(dt[12:14]), second=int(dt[15:17])).timestamp()


# Make the JWT claim set
def claim_info(file_hash, time_stamp):

    #- TBD: Time delivers seconds since unix epoch. Not all systems have the same epoch start date.  There
    #- may be a better way to time stamp the claims.
    issue_time = int(time())

    # See RFC 7519
    return {'iss':device_id,                 #Issuer -> This mvp is the issuer. Use it's secret key to authenticate.
            'aud':fop_jose_id,               #Audience -> identifies the cloud provider that will receive this claim.
            'exp':issue_time + 60,           #Expiration Time
            'sub':camera_device_id,          #Subject -> This mvp's camera is the subject
            'nbf':issue_time - 60,           #Not Before Time
            'iat':issue_time,                #Issued At
            'jti':str(uuid4()),              #JWT ID -> Don't accept duplicates by jti
            'file_dt':time_stamp,
            'file_hash':file_hash}

def get_file_hash(path_name):

    m = sha256()
    with open(path_name, 'rb') as f:
        for line in f:
            m.update(line)
            
    return standard_b64encode(m.digest()).decode('utf-8')

def get_jws(path_name):

    return jws.sign(claim_info(get_file_hash(path_name), extract_timestamp(path_name)), 
                    hmac_secret_key,
                    algorithm='HS256')

def upload_camera_image(path_name):

    with open(path_name, 'rb') as f:
        r = post('{}'.format(image_post_url), 
                 data={'auth_method':'JWS', 'auth_data':get_jws(path_name)}, 
                 files={'file':f}) 

    return r
