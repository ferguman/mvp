import threading
from time import sleep
from logging import getLogger

from importlib import import_module
from python.repl import start as repl_start
from python.logger import get_top_level_logger
from python.updater import updater_init 

def execute_main(args, default_device_name):

    # NOTE: The placement of this import statement is important. It is placed here because one 
    #       cannot assume that a config file exists when fopd.py is run. For example the 
    #       first time fopd.py is run on a new device there may not be a config
    #       file yet.  So make sure that execute_main is only called once in the program.
    #
    # TODO: Consider refacting the codebase so that hte config file is executed (e.g.
    #       config = {}
    #       exec(Path('config.py').read_text(), config)
    #       The above commands will put the configuration file objects into the config dictionary. 
    #       the config dictionary can then be made available as a global.  This would
    #       allow the fopd to re-load the config file with out having to restart.
    from config import system, device_name

    if default_device_name != device_name:
        # get a logger keyed to the device name and as a side affect attach a rotating
        # file handler.
        logger = get_top_level_logger(device_name)
    else:
        logger = getLogger(default_device_name)

    logger.info('fopd device id: {}'.format(system['device_id']))

    c = {'device_name': device_name}
    app_state = {'system': system, 'config': c, 'stop': False, 'silent_mode':args.silent, 'sys':{'cmd':None}}

    # create a Barrier that all the threads can syncronize on. This is to
    # allow threads such as mqtt or data loggers to get initialized before
    # other threads try to call them.
    #
    # Figure out how many active resources there are. Each active one needs to sync to the barrier.
    active_resource_count = 0
    for r in system['resources']:
        if r['enabled']:
            active_resource_count += 1

    # Each resource will use the barrier to signal when they have completed their initialization.
    # In addtion add one to the active resource count for the repl thread. It will also signal when it
    # has completed it's initialization.
    #
    logger.info('will start {} resource threads'.format(active_resource_count + 1))
    b = threading.Barrier(active_resource_count + 1, timeout=20) 

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
    tl.append(threading.Thread(target=repl_start, name='repl', args=(app_state, args.silent, b)))

    # Start all threads
    for t in tl:
        t.start()

    # Insert the updater (python remote deployment commands into the repl
    updater_init(app_state)


    # Stop here and Wait for non-daemon threads to complete.
    for t in tl:
        if not t.isDaemon():
            t.join()

    # All the non-daemon threads have exited so exit fopd
    logger.info('fopd shutdown complete')

    # Exit with an exit code of success (e.g. 0)
    return 0
