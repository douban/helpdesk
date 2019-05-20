# coding: utf-8

from functools import partial

from st2client.client import Client
from st2client.models.action import Execution  # NOQA
from st2client.models.auth import Token  # NOQA

from app.config import (ST2_BASE_URL, ST2_API_URL,
                        ST2_AUTH_URL, ST2_STREAM_URL,
                        ST2_API_KEY, ST2_CACERT)

# see the doc: https://github.com/StackStorm/st2/tree/master/st2client#python-client


class ST2ClientProxy:
    """NOTE: st2client has a very dirty hack that it stores token, apikey to os.environ,
        so we need re-force it."""

    def __init__(self, obj, **kw):
        self.obj = obj
        self.kw = kw

    def __getattr__(self, name):
        return self.__class__(getattr(self.obj, name), **self.kw)

    def __call__(self, *a, **kw):
        kw.update(self.kw)
        return self.obj(*a, **kw)


make_client = partial(Client, base_url=ST2_BASE_URL, api_url=ST2_API_URL,
                      auth_url=ST2_AUTH_URL, stream_url=ST2_STREAM_URL,
                      cacert=ST2_CACERT)
make_client_proxy = lambda **kw: ST2ClientProxy(make_client(**kw), **kw)  # NOQA

client = make_client_proxy(api_key=ST2_API_KEY)


def get_client(token):
    return make_client_proxy(token=token)


if __name__ == '__main__':
    print(client.actions.get_all())
