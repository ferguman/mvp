# Wrapper functions for PyNaCl (https://pynacl.readthedocs.io/en/stable/)

from base64 import standard_b64encode, standard_b64decode

from nacl import secret

from config.private_key import nsk_b64

def encrypt(plain_text: 'binary string') -> 'b64 string':

    return standard_b64encode(secret.SecretBox(standard_b64decode(nsk_b64)).encrypt(plain_text))

def decrypt(ciper_text) -> 'binary string': 

    return secret.SecretBox(standard_b64decode(nsk_b64)).decrypt(standard_b64decode(ciper_text))

def decrypt_dict_vals(d: dict, dict_keys_to_decrypt):

    new_dict = {}
    for key, val  in d.items():
        if key in dict_keys_to_decrypt:
            #- new_dict[key] = decrypt(val)
            new_dict[key] = decrypt(val).decode('utf-8')
        else:
            new_dict[key] = val

    return new_dict
