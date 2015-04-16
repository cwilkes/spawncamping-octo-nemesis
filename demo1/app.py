from flask import Flask, jsonify, request, redirect
import os
import logging
from services import UserService


__doc__ = """
Simple REST service for creating, listing, and showing users that have a name and email address
Uses redis for the backend service, the URL retrieved from the environment variable REDIS_URL or
the default localhost:6379
HTTP methods:
/ GET   list all users
/ POST  creates a user with the form parameters "name" and "email".  Returns a redirect to that URL
/<integer> GET  returns that user
/<integer> DELETE deletes that user
"""


app = Flask(__name__)
app.config.from_object(__name__)


def redis():
    return app.config['redis']


@app.route('/_info', methods=['GET', ])
def api_connection_info():
    return jsonify(redis().rs.connection_pool.connection_kwargs)


@app.route('/', methods=['GET', ])
def api_index():
    user_ids = sorted(redis().get_user_ids())
    user_links = list()
    for user_id in user_ids:
        user_links.append(dict(id=user_id, href='/%d' % (user_id, )))
    return jsonify(dict(users=user_links))


@app.route('/<int:user_id>', methods=['GET', ])
def api_get_user(user_id):
    return jsonify(redis().get_user(user_id))


@app.route('/', methods=['POST', ])
def api_create_user():
    try:
        name = request.form['name']
        email = request.form['email']
    except Exception as ex:
        response = jsonify(dict(error='Error getting name or email', exception=ex))
        response.status_code = 500
        return response
    user_id = redis().create_user(name, email)
    return redirect('/%d' % (user_id, ))


@app.route('/<int:user_id>', methods=['DELETE', ])
def api_delete_user(user_id):
    user = redis().delete_user(user_id)
    return jsonify(user)


def _create_logging_handler():
    class IPLoggingFilter(logging.Filter):
        def filter(self, record):
            record.ip = request.remote_addr
            return True
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter('%(asctime)-15s %(name)-5s %(levelname)-8s - %(ip)s - %(message)s'))
    handler.addFilter(IPLoggingFilter())
    return handler


if __name__ == '__main__':
    app.logger.addHandler(_create_logging_handler())
    app.logger.setLevel(logging.INFO)
    redis_host = os.getenv('R_HOST', 'localhost')
    redis_port = int(os.getenv('R_PORT', '6379'))
    redis_password = os.getenv('R_PASSWORD', None)
    print 'in main, host: %s, port: %d, password: %s' % (redis_host, redis_port, redis_password)
    app.config['redis'] = UserService(redis_host, port=redis_port, password=redis_password)
    app.run(host='0.0.0.0')