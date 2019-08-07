# This program iniailizes a mender based fopd system. It does the following:
# Check to see if there a hostname specifed in the /data/fopd/hostname file. If there is then
# it changes the hostname using the value found in this file. If there is no /data/fopd/hostname
# file then the program prompts the user for a hostname and sets it. 

# Usage: python3 mender_init.py

# 

# Restore the host name.

# 

# Use the hostname command to change the hostname
import subprocess
# if the /data/fopd/hostname file exists then use it.
#TODO take the hostname from /data/fopd/hostname file.
subprocess.run(
    ['sudo', './scripts/change_host_name.sh', 'fc1'])
# else
# prompt the user for a hostname and then set it. and create the /data/fopd/hostname file. 
