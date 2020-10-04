from argparse import ArgumentParser

def get_args():

    # Process the command line args
    parser = ArgumentParser()
    parser.add_argument('-s', '--silent', help='do not provide a console prompt,'\
                        + ' use this mode when running as a systemd service', \
                        action='store_true')
    parser.add_argument('-u', '--utility', type=str, 
                        choices=['create_private_key', 'create_random_uuid', 'create_system', 
                                 'create_service_file', 'decrypt', 'encrypt'],
                        help='perform a utility function.')
    parser.add_argument('-i', '--utility_input', type=str, 
                        help='Input for encrypt and decrypt utilities. Don''t quote input strings and use \ to escape special characters and spaces.')
    return parser.parse_args()
