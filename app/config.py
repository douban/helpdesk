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

PROVIDER = ''

# TODO: LDAP
# for LdapProviderMixin, to provide the ability to access user metadata like email addrs.

DEFAULT_EMAIL_DOMAIN = ''
# base url will be used by notifications to show web links
DEFAULT_BASE_URL = ''
FORCE_HTTPS = False
ADMIN_EMAIL_ADDRS = ''
FROM_EMAIL_ADDR = ''

NOTIFICATION_TITLE_PREFIX = ''

NO_AUTH_TARGET_OBJECTS = []

URL_RESET_PASSWORD = ''

AUTO_APPROVAL_TARGET_OBJECTS = []

TICKETS_PER_PAGE = 50

ACTION_TREE_CONFIG = ['功能导航', []]


try:
    from local_config import *   # NOQA
except ImportError as e:
    print('Import from local_config failed, %s' % str(e))
