from python.logger import get_top_level_logger
from python.repl import start
from python.utilities.create_private_key import create_private_key
from python.utilities.create_system import create_system

logger = get_top_level_logger('fopd')

def execute_utility(args):

    eval_state = {'stop':True, 'sys':{'cmd':None}}
    eval_state['utils'] = {'create_private_key':create_private_key}
    eval_state['utils']['create_system'] = create_system()
    eval_state['system'] = {}
    eval_state['config'] = {'device_name':'fopd'}

    # Run the repl and start with the selected utility. 
    start(eval_state, args.silent, start_cmd='utils.'+ args.utility +'()')

    exit()
