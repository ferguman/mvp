# Wrapper functions for PyNaCl (https://pynacl.readthedocs.io/en/stable/)

from base64 import standard_b64encode, standard_b64decode

from nacl import secret, utils

from data_location import configuration_directory_location

#+ from config.private_key import nsk_b64

def encrypt(plain_text: 'binary string') -> 'b64 string':

    with SecretKey() as nsk:
        return standard_b64encode(secret.SecretBox(bytes(nsk)).encrypt(plain_text))

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
    """ This Context makes the secret key available.  The location of the secret
        key file is assumed to be the configuration_direction_location specified in the
        settings file.  The context stores the
        secret key in a bytearray.  When the context exits it overwrites the 
        contents of the bytearray with zero to prevent malware from snooping the
        passcode.  Note: I don't know what happens to the in memory file contents,
        or the return value of the 'bytes()' calls in this module.
        Nor do I know what nacl does with it's reference to the secret key.
    """

    def __enter__(self) -> 'bytearray':

        #- with open('config/private_key', 'rb') as fp:
        with open(configuration_directory_location + 'private_key', 'rb') as fp:

            self.secret_key = bytearray(32)
            for i in range(0, 32):
                self.secret_key[i] = ord(fp.read(1))

            return self.secret_key

    def __exit__(self, exc_type, exc_value, exc_trace) -> None:

        for i in range(len(self.secret_key)):
                self.secret_key[i] = 0

        if exc_value:
            raise SecretKeyException(exc_value)
