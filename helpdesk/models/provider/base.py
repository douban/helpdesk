from type import List, Dict, Optional, Any, Tuple
from datetime import datetime

from helpdesk.libs.types import TicketExecResultInfo, TicketSummary, \
    TicketSchema, TicketExecInfo, TicketExecInfo, TicketExecResultInfo, \
    TicketTaskLog


class BaseProvider:
    provider_type = ''

    def __init__(self, **kwargs):
        pass

    def __str__(self):
        attrs = []
        for k in sorted(self.__dict__):
            if k.startswith('_'):
                continue
            v = getattr(self, k)
            v = '"%s"' % str(v) if type(v) in (str, datetime) else str(v)
            attrs.append('%s=%s' % (k, v))
        return '%s(%s)' % (self.__class__.__name__, ', '.join(attrs))

    __repr__ = __str__

    def get_default_pack(self):
        raise NotImplementedError()

    def get_tickets_summary(self, pack: Optional[str]) -> List[TicketSummary]:
        raise NotImplementedError()

    def get_tickets_schema(self, ticket_name: str) -> List[TicketSchema]:
        raise NotImplementedError()

    def run_ticket(self, ticket_name: str, parameters: Dict[str, Any]) -> TicketExecInfo:
        raise NotImplementedError()

    def generate_annotation(self, execution: TicketExecInfo) -> Dict[str, str]:
        raise NotImplementedError()

    def get_execution(self, execution_id: str) -> (Optional[TicketExecResultInfo], str):
        raise NotImplementedError()

    def get_execution_output(self, execution_id: str) -> TicketTaskLog:
        raise NotImplementedError()
