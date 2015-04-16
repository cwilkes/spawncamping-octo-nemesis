from flask import Flask, jsonify, request, redirect
import redis
import os
import simplejson as json
import logging


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


class UserService(object):
    def __init__(self, url):
        self.conn = redis.from_url(url)

    def delete_user(self, user_id):
        user = self.conn.get(self.user_url(user_id))
        if user:
            self.conn.delete(self.user_url(user_id))
            return user
        else:
            return dict(error='no user', id=user_id)

    def get_user(self, user_id):
        return json.loads(self.conn.get(self.user_url(user_id)))

    def create_user(self, name, email):
        user = dict(name=name, email=email)
        app.logger.info('Creating user %s', user)
        user_id = self.conn.incr('user_id_gen')
        app.logger.info('User id generated %s', user_id)
        self.conn.set(self.user_url(user_id), json.dumps(user))
        return user_id

    def get_user_ids(self):
        user_ids = list()
        # array of users, ie ['users/2', 'users/1']
        for full_user_path in self.conn.keys('users/*'):
            user_id_str = full_user_path[6:]
            user_ids.append(int(user_id_str))
        return user_ids

    @staticmethod
    def user_url(user_id):
        return 'users/%d' % (user_id, )


# redis://:redis@pub-redis-14008.us-east-1-4.2.ec2.garantiadata.com:14008
rs = UserService(os.getenv('REDIS_URL', 'redis://localhost:6379'))


@app.route('/', methods=['GET', ])
def api_index():
    user_ids = sorted(rs.get_user_ids())
    user_links = list()
    for user_id in user_ids:
        user_links.append(dict(id=user_id, href='/%d' % (user_id, )))
    return jsonify(dict(users=user_links))


@app.route('/<int:user_id>', methods=['GET', ])
def api_get_user(user_id):
    return jsonify(rs.get_user(user_id))


@app.route('/', methods=['POST', ])
def api_create_user():
    try:
        name = request.form['name']
        email = request.form['email']
    except Exception as ex:
        response = jsonify(dict(error='Error getting name or email', exception=ex))
        response.status_code = 500
        return response
    user_id = rs.create_user(name, email)
    return redirect('/%d' % (user_id, ))


@app.route('/<int:user_id>', methods=['DELETE', ])
def api_delete_user(user_id):
    user = rs.delete_user(user_id)
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
    app.run(host='0.0.0.0')