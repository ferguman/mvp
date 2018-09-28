from flask import Flask, render_template, __version__

class fopdwFlask(Flask):

    jinja_options = Flask.jinja_options.copy()

    jinja_options.update(dict(
        block_start_string = '(%',
        block_end_string = '%)',
        variable_start_string = '((',
        variable_end_string = '))',
        comment_start_string = '(#',
        comment_end_string = '#)',
    ))
    
app = fopdwFlask(__name__)
app.logger.info('starting Flask version {}'.format(__version__))

app_state = None

@app.route('/')
def home():
    return render_template('home.html', chart_list=app_state['sys']['chart_list'])

def run_flask(state):

    # take up the app_state from the caller
    global app_state
    app_state = state 

    # run Flask.  Note: this function does not return.
    # TODO: Figure out how to gracefully shut down Flask
    app.run(host='0.0.0.0')
