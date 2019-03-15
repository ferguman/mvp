from time import time

class LogFileEntryTable(object):

    def __init__(self, interval):
        self.interval = interval
       
    log_entries = {}

    def add_log_entry(self, func, entry_val):

        ''' This function adds values to the log dictionary and 
            creates a log entry if the logging interval has been exceeded.
            The idea is to use it for situations where one does not one to flood the
            logs with entries. Typically this occurs when an error occurs such that
            the error is to be logged but the system is not to stop.

            Here is a typical call -> add_log_entry(logger_error, 'hey this thing is failing every second')
        '''

        if entry_val not in self.log_entries.keys() or self.log_entries[entry_val] < time() - self.interval:
            self.log_entries[entry_val] = time()
            func('({} sec. throttle) '.format(self.interval) + entry_val)
