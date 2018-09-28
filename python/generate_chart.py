from os import getcwd
import pygal
from sys import exc_info
import requests
import json
from datetime import datetime

enable_display_unit_error_msg = None 

# TODO: Current the system supports converting from celsius to fahrenheit. As the need arises
#       add more unit conversions.
#
def apply_unit_conversion(val_tree, chart_info):

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

#Use a view in CouchDB to get the data
#use the first key for attribute type
#order descending so when limit the results will get the latest at the top

def generate_chart(couchdb_url, chart_info, logger):

    # Get the data from couch
    #
    couch_query = couchdb_url + '_design/doc/_view/attribute_value?'\
                     + 'startkey=["{0}","{1}",{2}]&endkey=["{0}"]&descending=true&limit=60'.format(
                     chart_info['attribute'], chart_info['couchdb_name'], '{}')
                     
    logger.debug('prepared couchdb query: {}'.format(couch_query))
    r = requests.get(couch_query)

    # TODO: the following prints out '<Response [200]>'. Need to wrap error checking around this call and suppress
    # printing on "normal" operation. What about long web requests???
    # print(r)

    try:
        global enable_display_unit_error_msg
        enable_display_unit_error_msg = True
        #- v_lst = [float(x['value']['value']) for x in r.json()['rows']]
        v_lst = [float(apply_unit_conversion(x, chart_info)) for x in r.json()['rows']]
        v_lst.reverse()
        ts_lst = [datetime.fromtimestamp(x['value']['timestamp']).strftime('%m/%d %I:%M %p') for x in r.json()['rows']]
        ts_lst.reverse()

        # line_chart = pygal.Line(interpolate='cubic')
        line_chart = pygal.Line()
        line_chart.title = chart_info['chart_title'] #'Temperature'
        line_chart.y_title= chart_info['y_axis_title'] #"Degrees C"
        line_chart.x_title= chart_info['x_axis_title'] #"Timestamp (hover over to display date)"
        line_chart.x_labels = ts_lst

        #need to reverse order to go from earliest to latest
        v_lst.reverse()

        line_chart.add(chart_info['data_stream_name'], v_lst)
        line_chart.render_to_file(getcwd() + '/web/static/' + chart_info['chart_file_name'])
    except:
        logger.error('Chart generation failed: {}'.format(exc_info()[0]))
