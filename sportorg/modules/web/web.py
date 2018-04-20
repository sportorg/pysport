from threading import Thread, main_thread
import time
import logging
from flask import Flask, request, jsonify

from sportorg.core.broker import Broker
from sportorg.models.memory import race
from sportorg import config
from . import cross_domain

app = Flask(__name__, static_url_path='', static_folder=config.base_dir('web', 'dist'))
log = logging.getLogger('werkzeug')
log.disabled = not config.DEBUG

updated_time = time.time()


def new_time():
    global updated_time
    updated_time = time.time()


Broker().subscribe('teamwork_sending', lambda send: new_time())


def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()


@app.route('/api/v1/updated_time')
@cross_domain(origin='*')
def updated_time_handler():
    is_alive = main_thread().is_alive()
    return jsonify({
        'updated_time': updated_time,
        'is_alive': is_alive
    })


@app.route('/api/v1/race')
@cross_domain(origin='*')
def data():
    return jsonify(race().to_dict())


@app.route('/api/v1/shutdown', methods=['POST', 'GET'])
@cross_domain(origin='*')
def shutdown():
    shutdown_server()
    return 'Server shutting down...'


@app.route('/')
@cross_domain(origin='*')
def root():
    return app.send_static_file('index.html')


def run():
    try:
        app.run()
    except Exception as e:
        logging.error(str(e))


def app_thread():
    return Thread(target=run, name=app.name)
