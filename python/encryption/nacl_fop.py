# Wrapper functions for PyNaCl (https://pynacl.readthedocs.io/en/stable/)

from base64 import standard_b64encode, standard_b64decode

from nacl import secret, utils

#+ from config.private_key import nsk_b64

"""-
def encrypt(plain_text: 'binary string') -> 'b64 string':

    return standard_b64encode(secret.SecretBox(standard_b64decode(nsk_b64)).encrypt(plain_text))
"""

def encrypt(plain_text: 'binary string') -> 'b64 string':

    with SecretKey() as nsk:
        return standard_b64encode(secret.SecretBox(bytes(nsk)).encrypt(plain_text))

""" -
def decrypt(ciper_text) -> 'binary string': 

    return secret.SecretBox(standard_b64decode(nsk_b64)).decrypt(standard_b64decode(ciper_text))
"""

def decrypt(ciper_text) -> 'binary string': 

    with SecretKey() as nsk:
        return secret.SecretBox(bytes(nsk)).decrypt(standard_b64decode(ciper_text))

def decrypt_dict_vals(d: dict, dict_keys_to_decrypt):

    #TODO - put a with SecretKey inside this routine so that the 
    #       secret key file isn't being opened and closed for each key

    new_dict = {}
    for key, val  in d.items():
        if key in dict_keys_to_decrypt:
            new_dict[key] = decrypt(val).decode('utf-8')
        else:
            new_dict[key] = val

    return new_dict

class SecretKeyException(Exception):
    pass

class SecretKey:

    def __enter__(self) -> 'bytearray':

        with open('config/private_key', 'rb') as fp:

            self.secret_key = bytearray(32)
            for i in range(0, 32):
                self.secret_key[i] = ord(fp.read(1))

            return self.secret_key

    def __exit__(self, exc_type, exc_value, exc_trace) -> None:

        for i in range(len(self.secret_key)):
                self.secret_key[i] = 0

        if exc_value:
            raise SecretKeyException(exc_value)
