from data_location import fopd_data_directory

# All configuration, recipes, state, 
# etc files are assumed to be contained within the fopd data directory.
#
configuration_directory_location = fopd_data_directory + 'config/'
recipes_directory_location = fopd_data_directory + 'recipes/'
state_directory_location = fopd_data_directory + 'state/'
local_web_chart_directory = 'web/static/'
local_web_image_directory = 'web/static/'
camera_image_directory = fopd_data_directory + 'pictures/'
log_directory = fopd_data_directory + 'logs/'
couchdb_local_config_file_directory = fopd_data_directory + 'couchdb/etc'
