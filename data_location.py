# This file is assumed to be placed in the home directory of the fopd code.  
# It tells fopd where the data directory is.

# Mender assumes a seperate partition named 'data'
fopd_data_directory = '/data/fopd/'

# The values below must include the /data/fopd/ part. All configuration, recipes, state, 
# etc files are assumed to be contained within the fopd data directory.
#
configuration_directory_location = '/data/fopd/config/'
recipes_directory_location = '/data/fopd/recipes/'
state_directory_location = '/data/fopd/state/'
local_web_chart_directory = 'web/static/'
local_web_image_directory = 'web/static/'
camera_image_directory = '/data/fopd/pictures/'


log_directory = '/data/fopd/logs/'
