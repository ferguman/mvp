# This program iniailizes a mender based fopd system. It does the following:
# Check to see if there a hostname specifed in the /data/fopd/hostname file. If there is then
# it changes the hostname using the value found in this file. If there is no /data/fopd/hostname
# file then the program prompts the user for a hostname and sets it. 

# Look at using overlays (OverlayFS in Linux).
# https://www.datalight.com/blog/2016/01/27/explaining-overlayfs-%E2%80%93-what-it-does-and-how-it-works/
# https://www.kernel.org/doc/Documentation/filesystems/overlayfs.txt
# The idea would be to create a directory (e.g. /etc/) that allows you to overlay
# files like hostname and hosts with files that exists on /data/etc.  This would allow
# changes to wifi, hostname, pi password, etc to remain in place on the Mender client
# after updates had been installed.:q
#
# The following command will mount /data/etc as the upper directory overlaying /etc:
#
# sudo mount -t overlay -o lowerdir=/etc,upperdir=/data/etc,workdir=/data/work overlay /etc
#
# You will want to run the above command as part of hte boot process. See https://yagrebu.net/unix/rpi-overlay.md
# for how this is done in the case of a ramfs ovelay.  This application is not a ramfs overlay but there
# should be some analgouse mechanism to mount over /etc before Linux starts looking into /etc.
#

# Usage: python3 fopd_init.py

# TODO: Add a password change for the pi linux account.

#- from os import path, getcwd, mkdir
from os import path, getcwd, system
import subprocess
from textwrap import dedent

from python.term_text_colors import green, red
from python.utilities.create_private_key import create_private_key
from data_location import fopd_data_directory 

init_tree = []

def prompt(s, inputs):
    print(dedent(s).format(*[red(i) for i in inputs]))
   
    #TODO - probably have to throw an exception in the case of cancel so that calling return knows to
    #       print 'fopd Init Cancelled and exit' when the exit condition is encountered
    cmd = input(green('fopd: ')) 
    if cmd.lower() != 'setup' and cmd.lower() != 'restore':
        return 'fopd Init Cancelled'

def restore():
    #TODO: Implement cloud restore
    return 'Cloud retore is not implemented.'


def fopd_init():
    
    if not path.isdir(fopd_data_directory):
        
        # Nothing is setup - there is no fopd directory on the data partition so do everything.
        # Ask for restoration method
        print('There is no fopd directory at {}. This indicates a new install or a'.format(fopd_data_directory))
        print('re-install of your fopd configuration. Enter one of the following:')
        print('{} to enter your fopd configuration information.'.format(red('setup')))
        print('{} to restore your fopd configuration from a backup.'.format(red('restore')))
        print('{} to exit'.format(red('exit')))

        cmd = input(green('fopd: ')) 
        if cmd.lower() != 'setup' and cmd.lower() != 'restore':
            return 'fopd Init Cancelled'


        if cmd.lower() == 'restore':
           init_tree.append('restore') 
         
           s = """\
              Enter one of the following:
              {} to restore from the cloud.
              {} to restore from a backup file that you specify.
              {} to exit'\n"""
           prompt(s, ['cloud', 'local', 'exit'])
           #- print(dedent(s).format(red('cloud'), red('local'), red('exit')))
    

        if cmd.lower() == 'setup':
            # manual setup

            # create fopd configuration directory
            system('sudo mkdir {}'.format(settings.fopd_data_directory))
            system('sudo chown pi:pi {}'.format(settings.fopd_data_directory))
            # result = subprocess.run(['sudo', './scripts/make_fop_dir.sh'])

            # Create private key file
            create_private_key() 

            return 'Ok'

    else:

        # Restore git settings
        # TODO: Check for existance of /data/fopd/gitconfig.sh.  If it exists then run it.

        # Restore the host name.
        print('Will search for an existing hostname and update it on this instance.')
        print('Enter yes to proceed, no to exit')
        cmd = input("\033[92m {} \033[00m" .format('fopd:')) 
        #- cmd = input('mender_init: ') 

        if cmd.lower() != 'yes':
            return 'Mender Init Cancelled'

        if not path.isdir('/data/fopd/'):
            print('There is no /data/fopd directory')
            print('Enter yes to create it, no to exit')
            cmd = input("\033[92m {} \033[00m" .format('fopd:')) 
            #- cmd = input('mender_init: ') 

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

print(fopd_init())
