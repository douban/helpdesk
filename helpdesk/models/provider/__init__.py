# coding: utf-8

import traceback

from helpdesk.libs.decorators import timed_cache
from helpdesk.models.provider.errors import InitProviderError, ResolvePackageError
from .st2 import ST2Provider
from .airflow import AirflowProvider
from .spincycle import SpinCycleProvider

_providers = {
    'st2': ST2Provider,
    'airflow': AirflowProvider,
    'spincycle': SpinCycleProvider,
}


@timed_cache(minutes=15)
def get_provider(provider, **kw):
    try:
        return _providers[provider](**kw)
    except Exception as e:
        raise InitProviderError(error=e, tb=traceback.format_exc(), description=f"Init provider error: {str(e)}")
