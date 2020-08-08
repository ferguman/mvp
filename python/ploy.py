# Python remote deployment (ploy)
# TODO - put python_a and python_b in the git ignore file.
#
# There are two python folders in the fopd directory: python_a and python_b
#
# Deployment consists of the following steps: 
# 1) The running fopd instance receives the command ploy(github_tag, TODO: specify the other arguments). This could be via the command line or
# via a remote connection such as MQTT.
# 2) If they don't exists then create the directories python_a and python_b and initiliaze next_pyhon_folder and current_python_folder
# 2) Download github_tag to data_locations.py(next_python_folder)
# 3) Swap the values in data_locations(current_python_folder) and data_locations(next_python_folder)
# 4) Set data_locations(play_state) = first_boot_pending
# 4) Exit fopd
#
# After step 4 above the next steps depend upon what is managing the invocation of fopd.py. If it is systemd and systemd is configured
# to restart fopd.py automatically then fopd.py will restart and assuming things work the update will have been done.
#
# Fail Back consists of the following steps:
# 1) the main program encounters an exception
# 2) if the exception is defined in the data_locations(non_failback_exceptions) then do nothing.
# 3) if the exception is not defined as a non_failback_exception then swap the values in
#    data_locations(current_python_folder) and data_locations(next_python_folder)
# 4) Set data_locations(ploy_state) = fail_back
# 5) Exit fopd
#
