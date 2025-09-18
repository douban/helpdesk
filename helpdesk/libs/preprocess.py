import logging
import traceback
from helpdesk.libs.sentry import report
from helpdesk.models.provider.errors import InitProviderError


logger = logging.getLogger(__name__)


class PreProcess:
    source = None

    async def process(self) -> str:
        raise NotImplementedError


pre_process = {}


def external_preprocess():
    try:
        from external_preprocess import DataLevelProcess

        pre_process["data_level"] = DataLevelProcess
    except Exception as e:
        logger.warning("Get external preprocess error: %s", e)
        report()


def get_preprocess(provider, **kw):
    external_preprocess()
    try:
        return pre_process[provider](**kw)
    except Exception as e:
        raise InitProviderError(
            error=e,
            tb=traceback.format_exc(),
            description=f"Init provider error: {str(e)}",
        )
