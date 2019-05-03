# coding: utf-8

from functools import partial

from st2client.client import Client
from st2client.models.action import Execution  # NOQA
from st2client.models.auth import Token  # NOQA

from app.config import (ST2_BASE_URL, ST2_API_URL,
                        ST2_AUTH_URL, ST2_STREAM_URL,
                        ST2_API_KEY, ST2_CACERT)


# see the doc: https://github.com/StackStorm/st2/tree/master/st2client#python-client

make_client = partial(Client, base_url=ST2_BASE_URL, api_url=ST2_API_URL,
                      auth_url=ST2_AUTH_URL, stream_url=ST2_STREAM_URL,
                      cacert=ST2_CACERT)

client = make_client(api_key=ST2_API_KEY)


def get_client(token):
    return make_client(token=token)


if __name__ == '__main__':
    print(client.actions.get_all())
