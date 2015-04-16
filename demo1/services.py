from redis import Redis
import simplejson as json
from flask import current_app


class UserService(object):
    def __init__(self, host, port=6379, password=None):
        self.rs = Redis(host, port=port, password=password)
        conn_args = self.rs.connection_pool.connection_kwargs
        print 'Redis host: %(host)s, port: %(port)s, password: %(password)s' % conn_args

    def delete_user(self, user_id):
        user = self.get_user(user_id)
        if user:
            self.rs.delete(self.user_url(user_id))
            return user
        else:
            return dict(error='no user', id=user_id)

    def get_user(self, user_id):
        return json.loads(self.rs.get(self.user_url(user_id)))

    def create_user(self, name, email):
        user = dict(name=name, email=email)
        current_app.logger.info('Creating user %s', user)
        user_id = self.rs.incr('user_id_gen')
        current_app.logger.info('User id generated %s', user_id)
        self.rs.set(self.user_url(user_id), json.dumps(user))
        return user_id

    def get_user_ids(self):
        user_ids = list()
        # array of users, ie ['users/2', 'users/1']
        for full_user_path in self.rs.keys('users/*'):
            user_id_str = full_user_path[6:]
            user_ids.append(int(user_id_str))
        return user_ids

    @staticmethod
    def user_url(user_id):
        return 'users/%d' % (user_id, )