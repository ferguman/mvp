from flask import Flask, render_template, __version__
from python.logger import get_the_fopd_log_handler
from logging import INFO

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

# Intercept Flask's output
#
# app.logger.addHandler(get_the_fopd_log_handler())

app.logger.info('running Flask verison {}'.format(__version__))

@app.route('/')
def home():
    return render_template('home.html')

#- app.run() does not return.
#- app.run(host='0.0.0.0')
