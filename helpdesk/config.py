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

ADMIN_ROLES = ['admin', 'system_admin', 'Admin']

PARAM_FILLUP = {}
TICKET_CALLBACK_PARAMS = ('helpdesk_ticket_callback_url', 'helpdeskTicketCallbackUrl')

PROVIDER = ''
ENABLED_PROVIDERS = ('st2', 'airflow', 'spincycle')

DEFAULT_EMAIL_DOMAIN = ''
# base url will be used by notifications to show web links
DEFAULT_BASE_URL = ''
ADMIN_EMAIL_ADDRS = ''

WEBHOOK_URL = ''

FROM_EMAIL_ADDR = 'sysadmin+helpdesk@example.com'
SMTP_SERVER = 'localhost'
SMTP_SERVER_PORT = 25
SMTP_SSL = False
SMTP_CREDENTIALS = ''

NOTIFICATION_TITLE_PREFIX = ''
NOTIFICATION_METHODS = []

OPENID_PRIVIDERS = []


AUTO_APPROVAL_TARGET_OBJECTS = []
TICKETS_PER_PAGE = 50

ACTION_TREE_CONFIG = ['功能导航', []]

AIRFLOW_SERVER_URL = os.getenv('HELPDESK_AIRFLOW_SERVER_URL', 'http://airflow.example.com')
AIRFLOW_USERNAME = os.getenv('HELPDESK_AIRFLOW_USERNAME', 'sysadmin')
AIRFLOW_PASSWORD = os.getenv('HELPDESK_AIRFLOW_PASSWORD')
AIRFLOW_DEFAULT_DAG_TAG = 'helpdesk'

SPINCYCLE_RM_URL = os.getenv("HELPDESK_SPINCYCLE_SERVER_URL", "https://spincycle.example.com")
SPINCYCLE_USERNAME = os.getenv('HELPDESK_SPINCYCLE_USERNAME', 'sysadmin')
SPINCYCLE_PASSWORD = os.getenv('HELPDESK_SPINCYCLE_PASSWORD')
SPINCYCLE_RM_CERT_PATH = os.getenv("HELPDESK_SPINCYCLE_RM_CERT_PATH")

try:
    from local_config import *  # NOQA
except ImportError as e:
    print('Import from local_config failed, %s' % str(e))
