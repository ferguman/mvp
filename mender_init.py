# This program iniailizes a mender based fopd system. It does the following:
# Check to see if there a hostname specifed in the /data/fopd/hostname file. If there is then
# it changes the hostname using the value found in this file. If there is no /data/fopd/hostname
# file then the program prompts the user for a hostname and sets it. 

# Usage: python3 mender_init.py

from os import path, getcwd, mkdir
import subprocess
# 
def mender_init():


    # Restore git settings
    # TODO: Check for existance of /data/fopd/gitconfig.sh.  If it exists then run it.

    # Restore the host name.
    print('Will search for an existing hostname and update it on this instance.')
    print('Enter yes to proceed, no to exit')
    cmd = input('mender_init: ') 

    if cmd.lower() != 'yes':
        return 'Mender Init Cancelled'

    if not path.isdir('/data/fopd/'):
        print('There is no /data/fopd directory')
        print('Enter yes to create it, no to exit')
        cmd = input('mender_init: ') 

        if cmd.lower() != 'yes':
            return 'Mender Init Cancelled'

        result = subprocess.run(['sudo', './scripts/make_fop_dir.sh'])

            #- print('failed to create /data/fopd')
            #- return 'Mender Init Failed'

        return 'Ok'

    return 'Ok'






# if the /data/fopd/hostname file exists then use it.
#TODO take the hostname from /data/fopd/hostname file.
#+ subprocess.run(
#+    ['sudo', './scripts/change_host_name.sh', 'fc1'])
# else
# prompt the user for a hostname and then set it. and create the /data/fopd/hostname file. 

print(mender_init())
