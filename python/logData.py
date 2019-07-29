from sys import path, exc_info
from os import getcwd
from datetime import tzinfo, datetime
import requests
import json

from config import local_couchdb_url, couchdb_username_b64_cipher, couchdb_password_b64_cipher 
from python.encryption.nacl_fop import decrypt
from python.logger import get_sub_logger 

logger = get_sub_logger(__name__)

# TBD - Need to make add capability to system to log to a file.
def logFile(timestamp, name, status, attribute, value, comment):
    #TBD - Need to put a file rotation scheme in place for the text file.
    #TBD - I'm not sure this is thread safe.  If the light controller and the logSensor
    #      threads both call it can things get messed up?:

    try:
        f = open(getcwd() + '/data/data.txt', 'a')
        s = name + ", " + status + ", " + attribute + ", " + value + "," + comment
        logger.debug('appending data: {} to file: {}'.format(s, f))
        f.write(s + "\n")
        f.close()
    except:
        logger.error('Error writing to data file: {}'.format(exc_info()[0]))


def logDB(r, comment=''):

    log_record = {'timestamp' : r['ts'],
                  'name' :      '{} {}'.format(r['subject'],r['attribute']),
                  'status' :    'Success',
                  'attribute' : r['attribute'],
                  'value' :     r['value'],
                  'units' :     r['units'],
                  'comment' :   comment}

    logger.info('couchd db write: {}, {}, {}, {}, {}'.format(log_record['name'], 
                                                             log_record['status'], log_record['attribute'], 
                                                             log_record['value'], log_record['comment']))

    json_data = json.dumps(log_record)
    headers = {'content-type': 'application/json'}
    
    """
    if there is a network problem like a DNS failure, or refused connection the Requests library will
    raise a ConnectionError exception.  With invalid HTTP responses, Requests will also raise an HTTPError 
    exception, but these are rare.  If a request times out, a Timeout exception will be raised.
    If and when a request exceeds the preconfigured number of maximum redirections, then a TooManyRedirects
    exception will be raised.
    """

    try:
        r = requests.post(local_couchdb_url, data = json_data, headers=headers, 
                          auth=(decrypt(couchdb_username_b64_cipher).decode('utf-8'),
                                decrypt(couchdb_password_b64_cipher).decode('utf-8')))
        if r.status_code != 201:
            logger.error('local couchdb return an error code: {}, {}...'.format(r.status_code, r.text[0:100]))
    except:
        logger.error('cannot post data to the local couchdb: {}, {}'.format(exc_info()[0], exc_info()[1]))
