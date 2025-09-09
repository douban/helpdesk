# coding: utf-8

import traceback

from helpdesk.libs.decorators import timed_cache
from helpdesk.models.provider.errors import InitProviderError
from helpdesk.models.provider.airflow import AirflowProvider

_providers = {
    'airflow': AirflowProvider
}


@timed_cache(minutes=15)
def get_provider(provider, **kw):
    try:
        return _providers[provider](**kw)
    except Exception as e:
        raise InitProviderError(error=e, tb=traceback.format_exc(), description=f"Init provider error: {str(e)}")
