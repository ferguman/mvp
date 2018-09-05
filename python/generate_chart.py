from os import getcwd
import pygal
from sys import exc_info
import requests
import json

from python.logger import get_sub_logger 

#Use a view in CouchDB to get the data
#use the first key for attribute type
#order descending so when limit the results will get the latest at the top

logger = get_sub_logger(__name__)

def generate_chart(couchdb_url, chart_info):

    # Get the temperature data from couch
    #
    #- r = requests.get(couchdb_url + '_design/doc/_view/attribute_value?'
    #-                 + 'startkey=["{}",{}]&endkey=["{}"]&descending=true&limit=60'.format(\
    #-                 chart_info['couch_key_name'], '{}', chart_info['couch_key_name']))

    couch_query = couchdb_url + '_design/doc/_view/attribute_value?'\
                     + 'startkey=["{0}","{1}",{2}]&endkey=["{0}","{1}"]&descending=true&limit=60'.format(\
                     chart_info['device']['attributes'][chart_info['attribute_index']]['name'],\
                     chart_info['device']['name'],\
                     '{}')
    logger.debug('prepared couchdb query: {}'.format(couch_query))
    r = requests.get(couch_query)

    # TBD: the following prints out '<Response [200]>'. Need to wrap error checking around this call and suppress
    # printing on "normal" operation. What about long web requests???
    # print(r)

    try:
        v_lst = [float(x['value']['value']) for x in r.json()['rows']]
        v_lst.reverse()
        ts_lst = [x['value']['timestamp'] for x in r.json()['rows']]
        ts_lst.reverse()

        line_chart = pygal.Line()
        line_chart.title = chart_info['chart_title'] #'Temperature'
        line_chart.y_title= chart_info['y_axis_title'] #"Degrees C"
        line_chart.x_title= chart_info['x_axis_title'] #"Timestamp (hover over to display date)"
        line_chart.x_labels = ts_lst

        #need to reverse order to go from earliest to latest
        v_lst.reverse()

        line_chart.add(chart_info['data_stream_name'], v_lst)
        line_chart.render_to_file(getcwd() + '/web/' + chart_info['chart_file_name'])
    except:
        logger.error('Chart generation failed: {}'.format(exc_info()[0]))
