# When fopd is run as a Mender client it needs to preserve certain data such as
# the host name across updates.  Mender updates are done by replacing the currently
# acive Linux partition with a new one.  In order to preserve certain data such as hostname that
# is stored within the Linux partition (in this case at /etc/hostname) the fopd Mender system
# assumes that this non-fungible data is stored on the /data partition.  Mender data
# partitions are not affected by updates.
#
# This script overwrites the existing hosts and hostname files with the ones sourced from /data.
# The Linux kernel sets the hostname before it mounts /data so it does not work
# to make /etc/hostname and /etc/hosts symbolic links to /data/etc/hostname and /uboot/etc/hosts.
#

import subprocess

def copy_file(source_path, destination_path):
   cp = subprocess.run('cp -f {} {}'.format(source_path, destination_path), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
   """
   if cp.returncode != 0:
      print('ERROR: Can not copy {} to {}'.format(source_path, destination_path))
      print('{}'.format(cp.stderr))
   """

copy_file('/data/etc/hostname', '/etc/hostname')
copy_file('/data/etc/hosts', '/etc/hosts')


cp = subprocess.run('/bin/hostname -f /etc/hostname', stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
