from os import path, getcwd

from jinja2 import Environment, FileSystemLoader

def create_service_file(): 

    """Create a Systemd service file named fopd.servic."""

    sd = {}
    sd['working_directory'] = '/home/pi/fopd'
    sd['user'] = 'pi'
    sd['exec_start_cmd'] = '/home/pi/fopd/fopd/bin/python'
    sd['exec_start_target'] = '/home/pi/fopd/fopd.py --silent'
    sd['restart_value'] = 'on-failure'

    
    # generate the service file path
    sfp = path.join('/etc/systemd/system/', 'fopd.service')
    sfcp = path.join(getcwd(), 'config/systemd.service')
    if path.isfile(sfcp):
        print('WARNING: It looks like a service file already exists at {}.\n'.format(sfcp),
              'If you proceed that file will be overwritten.\n',
              'Enter yes to proceed, no to exit')
        cmd = input('fopd: ')

        if cmd.lower() != 'yes':
            return 'CANCELED'

    # Create a jinja2 environment and compile the template 
    env = Environment(
       loader=FileSystemLoader(path.join(getcwd(), 'config')),
       trim_blocks=True
       ) 
    template = env.get_template('/templates/systemd.j2')

    # Render the jinja2 template into a new systemd service file 
    with open(sfcp, 'w') as f:
        f.write(template.render(config=sd))

    print('A systemd service file has been created at {}.\n'.format(sfcp),
          '\n',
          'You can install fopd as a systemd service by performing the following two commands:\n\n',
          'sudo cp {} {}\n'.format(sfcp, sfp),
          'sudo systemctl enable fopd\n',
          '\n',
          'The following commands allow you to control your service:\n',
          'sudo systemctl start fopd -> to start the service\n',
          'sudo systemctl stop fopd -> to stop the service\n',
          'sudo systemctl status fopd -> display service status')

    return 'OK'
