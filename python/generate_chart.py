from os import getcwd, path
import pygal
from sys import exc_info
import requests
import json
from datetime import datetime

from python.encryption.nacl_fop import decrypt

from data_location import local_web_chart_directory
#- from data_location import web_directory_location
from config import local_couchdb_url, couchdb_username_b64_cipher, couchdb_password_b64_cipher 

enable_display_unit_error_msg = None 

# TODO: Current the system supports converting from celsius to fahrenheit. As the need arises
#       add more unit conversions.
#
def apply_unit_conversion(val_tree, chart_info, logger):

    global enable_display_unit_error_msg 

    if 'display_units' in chart_info:
        if chart_info['display_units'].lower() == 'fahrenheit':
            if 'units' in val_tree['value']:
                if val_tree['value']['units'].lower() == 'celsius':
                   return  (float(val_tree['value']['value']) * 9.0/5.0) + 32
                elif val_tree['value']['units'].lower() == 'fahrenheit':
                   return val_tree['value']['value']
                else:
                    # Limit error unit related error messages to once per chart
                    if enable_display_unit_error_msg:
                        logger.error('cannot convert fahrenheit to: {}'.format(val_tree['value']['units']))
                        enable_display_unit_error_msg = False 
                    return val_tree['value']['value']
            else:
                return val_tree['value']['value']
        else:
            # Limit error unit related error messages to once per chart
            if enable_display_unit_error_msg:
                logger.error('non supported display_unit value: {}'.format(chart_info['display_unit']))
                enable_display_unit_error_msg = False 
            return val_tree['value']['value']
    else:
        return val_tree['value']['value']

def get_chart_data(couchdb_url, chart_info, logger):

    # Get the data from couch
    #
    couch_query = couchdb_url + '/_design/doc/_view/attribute_value?'\
                     + 'startkey=["{0}","{1}",{2}]&endkey=["{0}"]&descending=true&limit=60'.format(
                     chart_info['attribute'], chart_info['couchdb_name'], '{}')
                     
    logger.debug('prepared couchdb query: {}'.format(couch_query))
    
    try:
        r = requests.get(couch_query,
                         auth=(decrypt(couchdb_username_b64_cipher).decode('utf-8'),
                         decrypt(couchdb_password_b64_cipher).decode('utf-8')))

        if r.status_code != 200: 
            logger.error('local couchdb return an error code: {}, {}...'.format(r.status_code, r.text[0:100]))
            return None
        else:
            return r.json()

    except:
        logger.error('Cannot connect to the local Couchdb instance: {}, {}'.format(exc_info()[0], exc_info()[1]))
        return None


# Use a view in CouchDB to get the data
#use the first key for attribute type
#order descending so when limit the results will get the latest at the top

def generate_chart(couchdb_url, chart_info, logger):

    logger.debug('generating web charts')

    try:

        data =  get_chart_data(couchdb_url, chart_info, logger)
        if data:
            
            global enable_display_unit_error_msg
            enable_display_unit_error_msg = True
            v_lst = [float(apply_unit_conversion(x, chart_info, logger)) for x in data['rows']]

            ts_lst = [datetime.fromtimestamp(x['value']['timestamp']).strftime('%m/%d %I:%M %p')\
                      for x in data['rows']]
            ts_lst.reverse()

            # line_chart = pygal.Line(interpolate='cubic')
            line_chart = pygal.Line(x_label_rotation=20, show_minor_x_labels=False)
            line_chart.title = chart_info['chart_title']
            line_chart.y_title= chart_info['y_axis_title']
            line_chart.x_title= chart_info['x_axis_title']

            line_chart.x_labels = ts_lst
            # Major label every 8'th time point
            line_chart.x_labels_major = ts_lst[::8]

            #need to reverse order to go from earliest to latest
            v_lst.reverse()

            line_chart.add(chart_info['data_stream_name'], v_lst)
            #- line_chart.render_to_file(getcwd() + '/web/static/' + chart_info['chart_file_name'])


            line_chart.render_to_file(path.join(local_web_chart_directory, chart_info['chart_file_name']))
            #- line_chart.render_to_file(path.join(web_directory_location, chart_info['chart_file_name']))

        else:
            logger.error('No chart data available')
    except:
        logger.error('Chart generation failed: {}, {}'.format(exc_info()[0], exc_info()[1]))
