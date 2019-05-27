# coding: utf-8

import os


DEBUG = DEVELOP_MODE = False
SENTRY_DSN = ''

APP_BASE = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

avatar_url_func = lambda username: ''  # NOQA

DATABASE_URL = 'sqlite:///tmp/helpdesk.db'
# postgres://user:pass@localhost/dbname
# mysql://user:pass@localhost/dbname

SYSTEM_USER = 'admin'
SYSTEM_USER_PASSWORD = 'password'

ADMIN_ROLES = ['admin', 'system_admin']

PARAM_FILLUP = {}


try:
    from local_config import *   # NOQA
except ImportError as e:
    print('Import from local_config failed, %s' % str(e))
