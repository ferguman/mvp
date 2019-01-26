from flask import Flask, render_template, __version__, make_response
from python.logger import get_sub_logger 

class fopdwFlask(Flask):

    jinja_options = Flask.jinja_options.copy()

    # change the server side Jinja template code markers so that we can use Vue.js on the client.
    # Vue.js uses {{ }} as code markers so we don't want Jinja to interpret them.
    jinja_options.update(dict(
        block_start_string = '(%',
        block_end_string = '%)',
        variable_start_string = '((',
        variable_end_string = '))',
        comment_start_string = '(#',
        comment_end_string = '#)',
    ))

logger = get_sub_logger(__name__)

def start(app_state, args, barrier):

    #- print('starting Flask version ...')
    #- app.logger.info('starting Flask version {}'.format(__version__))
    logger.info('starting Flask version {}'.format(__version__))

    app = fopdwFlask(__name__)

    @app.route('/')
    def home():

        if args['chart_list_source']:
            cl = app_state[args['chart_list_source']]['chart_list']
        else:
            cl = [] 
        resp = make_response(render_template('home.html', chart_list=cl, num_of_charts=len(cl)))
        #- resp = make_response(render_template('home.html', chart_list=app_state[args['chart_list_source']]['chart_list']))
        resp.headers['Cache-Control'] = 'max-age:0, must-revalidate'
        return resp

    # Tell all the other threads that you are ready to go.
    #- barrier.wait()
    try:
        barrier.wait()
    except Exception as e:
        logger.error('Cannot start Flask because one or more other resources did not start')
        return

    # Start the Flask application. Note: app.run does not return.
    app.run(host=args['host'], port=args['port'])
