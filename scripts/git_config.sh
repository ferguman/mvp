#!/bin/bash

git config --global user.email $1 
git config --global user.name $2 

# Now put a copy of the file on the data partition so that future mender updates can restore the git settings
# to the user specified values.
echo "#!/bin/bash
git config --global user.email $1 
git config --global user.name $2" > $3/git_config.sh 

chmod 755 $3/git_config.sh
