# coding: utf-8

import traceback

from helpdesk.libs.decorators import timed_cache
from helpdesk.models.provider.errors import InitProviderError, ResolvePackageError
from .airflow import AirflowProvider
from .spincycle import SpinCycleProvider

_providers = {
    'airflow': AirflowProvider,
    'spincycle': SpinCycleProvider,
}


@timed_cache(minutes=15)
def get_provider(provider, **kw):
    try:
        return _providers[provider](**kw)
    except Exception as e:
        raise InitProviderError(error=e, tb=traceback.format_exc(), description=f"Init provider error: {str(e)}")
