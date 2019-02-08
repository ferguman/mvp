import threading
from importlib import import_module
from python.repl import start as repl_start
from python.logger import get_top_level_logger

def execute_main(args):

    # NOTE: This import is unusual. It is placed here because one cannot assume that that a config file
    #       exists when fopd.py is run. For example the first time fopd.py is run there may not be a config
    #       file yet.  So make sure that execute_main is only called once in the program.
    from config.config import system, device_name

    logger = get_top_level_logger(device_name)

    logger.info('############## starting farm operation platform device ################')

    logger.info('fopd device id: {}'.format(system['device_id']))

    c = {'device_name': device_name}
    app_state = {'system': system, 'config': c, 'stop': False, 'silent_mode':args.silent, 'sys':{'cmd':None}}

    # create a Barrier that all the threads can syncronize on. This is to
    # allow threads such as mqtt or data loggers to get initialized before
    # other threads try to call them.
    #
    active_resource_count = 0
    for r in system['resources']:
        if r['enabled']:
            active_resource_count += 1
    #- b = threading.Barrier(len(system['resources']), timeout=20) 
    b = threading.Barrier(active_resource_count, timeout=20) 

    # Each resource is implemented as a thread. Setup all the threads.
    tl = []
    for r in system['resources']:

        m = import_module(r['imp'])

        if r['enabled']:
            if r['daemon']:
                tl.append(threading.Thread(target=m.start, daemon=r['daemon'], name=r['args']['name'], args=(app_state, r['args'], b)))
            else:
                tl.append(threading.Thread(target=m.start, name=r['args']['name'], args=(app_state, r['args'], b)))

    # start the built in REPL interpretter.
    tl.append(threading.Thread(target=repl_start, name='repl', args=(app_state, args.silent)))

    # Start all threads
    for t in tl:
        t.start()
        
    logger.info('fopd startup complete')

    # Wait for non-daemon threads to complete.
    for t in tl:
        if not t.isDaemon():
            t.join()

    logger.info('fopd shutdown complete')

    return 0
