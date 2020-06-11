# coding: utf-8

from helpdesk.libs.decorators import timed_cache


from .st2 import ST2Provider
from .airflow import AirflowProvider
from .spincycle import SpinCycleProvider

PROVIDERS = {
    'st2': ST2Provider,
    'airflow': AirflowProvider,
    'spincycle': SpinCycleProvider,
}


@timed_cache(minutes=15)
def get_provider(provider, **kw):
    return PROVIDERS[provider](**kw)
