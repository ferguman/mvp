from nacl import secret, utils
from base64 import standard_b64encode

def create_random_key() -> 'b64 string':

    #- return standard_b64encode(utils.random(secret.SecretBox.KEY_SIZE))
    return utils.random(secret.SecretBox.KEY_SIZE)
