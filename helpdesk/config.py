# coding: utf-8

import os

DEBUG = DEVELOP_MODE = False
SENTRY_DSN = ''
SESSION_SECRET_KEY = ''
SESSION_TTL = 3600
APP_BASE = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

TRUSTED_HOSTS = '127.0.0.1'

TIME_ZONE = 'Asia/Shanghai'
TIME_FORMAT = '%Y-%m-%d %H:%M:%S %z %a'

ALLOW_ORIGINS = []  # use ['*'] to allow any origin.
ALLOW_ORIGINS_REG = None

avatar_url_func = lambda email: ''  # NOQA
oauth_username_func = lambda id_token: id_token['name']  # NOQA
get_user_email = lambda username: username + '@example.com'  # NOQA

DATABASE_URL = 'mysql://root:root@localhost/helpdesk'
# postgres://user:pass@localhost/dbname
# mysql://user:pass@localhost/dbname

ADMIN_ROLES = ['admin', 'system_admin', 'Admin']

PARAM_FILLUP = {}
TICKET_CALLBACK_PARAMS = ('helpdesk_ticket_callback_url', 'helpdeskTicketCallbackUrl')

ENABLED_PROVIDERS = ()

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

WEBHOOK_EVENT_URL = ""

OPENID_PRIVIDERS = {}
AUTHORIZED_EMAIL_DOMAINS = ["@example.com"]

AUTO_APPROVAL_TARGET_OBJECTS = []
TICKETS_PER_PAGE = 50

ACTION_TREE_CONFIG = ['功能导航', []]

ADMIN_POLICY = 1
DEPARTMENT_OWNERS = {"test_department": "department_user"}

SYSTEM_USER = 'admin'
SYSTEM_PASSWORD = 'password'
ST2_DEFAULT_PACK = ''
ST2_WORKFLOW_RUNNER_TYPES = []
ST2_API_KEY = ''
ST2_CACERT = ''
ST2_BASE_URL = 'https://st2.example.com'
ST2_API_URL = None
ST2_AUTH_URL = None
ST2_STREAM_URL = None
ST2_USERNAME = ''
ST2_PASSWORD = ''
ST2_EXECUTION_RESULT_URL_PATTERN = '{base_url}/#/code/result/{execution_id}'
ST2_TOKEN_TTL = 24 * 3600

AIRFLOW_SERVER_URL = 'https://airflow.example.com'
AIRFLOW_USERNAME = ''
AIRFLOW_PASSWORD = ''
AIRFLOW_DEFAULT_DAG_TAG = 'helpdesk'

SPINCYCLE_RM_URL = "https://spincycle.example.com"
SPINCYCLE_USERNAME = ''
SPINCYCLE_PASSWORD = ''


try:
    from local_config import *  # NOQA
except ImportError as e:
    print('Import from local_config failed, %s' % str(e))
