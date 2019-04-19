# coding: utf-8

import os


DEBUG = DEVELOP_MODE = False
SENTRY_DSN = ''

APP_BASE = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


try:
    from local_config import *   # NOQA
except ImportError as e:
    print('Import from local_config failed, %s' % str(e))
