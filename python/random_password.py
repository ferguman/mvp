import secrets
import string 

char_classes = (string.ascii_lowercase,
                string.ascii_uppercase,
                string.digits,
                string.punctuation)

#- size = lambda: secrets.choice(range(16))                    # Chooses a password length.
char = lambda: secrets.choice(secrets.choice(char_classes)) # Chooses one character, uniformly selected from each of the included character classes.
#- pw   = lambda: ''.join([char() for _ in range(size())])     # Generates the variable-length password.

def generate_password(pwd_len):
    if pwd_len >= 16 and pwd_len <= 128:
        return ''.join([char() for _ in range(pwd_len)])
    elif pwd_len <= 15:
        # step up to min lenght of 16
        return ''.join([char() for _ in range(16)])
    else:
        # step down to max length of 128
        return ''.join([char() for _ in range(128)])
        
