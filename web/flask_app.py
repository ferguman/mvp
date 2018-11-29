from flask import Flask, render_template, __version__, make_response

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
    
#- app = fopdwFlask(__name__)
#- app.logger.info('starting Flask version {}'.format(__version__))
"""
app_state = None

@app.route('/')
def home():

    resp = make_response(render_template('home.html', chart_list=app_state['sys']['chart_list']))
    resp.headers['Cache-Control'] = 'max-age:0, must-revalidate'
    return resp
"""

def start(app_state, args, barrier):

    app = fopdwFlask(__name__)
    app.logger.info('starting Flask version {}'.format(__version__))

    @app.route('/')
    def home():

        resp = make_response(render_template('home.html', chart_list=app_state['sys']['chart_list']))
        resp.headers['Cache-Control'] = 'max-age:0, must-revalidate'
        return resp

    # Tell all the other threads that you are ready to go.
    barrier.wait()

    # Start the Flask application. Note: app.run does not return.
    app.run(host=args['host'], port=args['port'])
