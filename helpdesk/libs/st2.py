# coding: utf-8

from urllib.parse import urljoin
from functools import partial

from st2client.client import Client
from st2client.models.action import Execution  # NOQA
from st2client.models.auth import Token  # NOQA

from helpdesk.config import (
    ST2_BASE_URL,
    ST2_API_URL,
    ST2_AUTH_URL,
    ST2_STREAM_URL,
    ST2_API_KEY,
    ST2_CACERT,
)

# see the doc: https://github.com/StackStorm/st2/tree/master/st2client#python-client
make_client = partial(
    Client,
    base_url=ST2_BASE_URL,
    api_url=ST2_API_URL or urljoin(ST2_BASE_URL, 'api'),
    auth_url=ST2_AUTH_URL or urljoin(ST2_BASE_URL, 'auth'),
    stream_url=ST2_STREAM_URL or urljoin(ST2_BASE_URL, 'stream'),
    cacert=ST2_CACERT)


def get_api_client(api_key=None):
    return make_client(api_key=api_key or ST2_API_KEY)


def get_client(token=None):
    return make_client(token=token)
