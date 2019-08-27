#!/bin/bash

git config --global user.email $1 
git config --global user.name $2 

# TODO: It's not a good idea to store plaintext git credentials on the fopd. Most user's won't use 
# git so this stuff only would be of some small help to developers.  So.... if you are going to store
# git configuraiton data such as this then you will need to encrypt it to a user supplied key. Don't use the
# fopd private key.
#
# Now put a copy of the file on the data partition so that future mender updates can restore the git settings
# to the user specified values.
# echo "#!/bin/bash
# git config --global user.email $1 
# git config --global user.name $2" > $3/git_config.sh 

# chmod 755 $3/git_config.sh
