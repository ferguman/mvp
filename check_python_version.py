from sys import version_info

# Check that the intepreter is 3.5 or later.
#
def check_python_version():

    py_ver = version_info

    if py_ver[0] < 3 or (py_ver[0] == 3 and py_ver[1] < 5):
        print('ERROR. Detected Python version: {}.{}.{}. The fopd code must be run by Python 3.5 or later.'.\
              format(py_ver[0], py_ver[1], py_ver[2]) + ' Make sure you use python3 or later '\
              + 'to invoke the program.')
        exit(1)
