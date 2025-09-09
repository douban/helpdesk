from typing import List, Dict, Optional, Any
from datetime import datetime

from helpdesk.libs.types import TicketExecResultInfo, ActionInfo, \
    ActionSchema, TicketExecInfo, TicketTaskLog


class BaseProvider:
    """
    action: capbility to execute a seirion of tasks
    ticket: action with args

    if action is class in python, ticket is the instance of this class
    """
    provider_type = None

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

    def get_default_pack(self) -> str:
        "provider default pack supported"
        raise NotImplementedError()

    def get_actions_info(self, pack: Optional[str]) -> List[ActionInfo]:
        "get actions simple info"
        raise NotImplementedError()

    def get_actions_schema_by_pack(self, pack_name: str) -> List[ActionSchema]:
        raise NotImplementedError()

    def get_action_schema(self, action_name: str) -> Optional[ActionSchema]:
        raise NotImplementedError()

    def exec_ticket(self, ticket_name: str, parameters: Dict[str, Any]) -> TicketExecInfo:
        "run action with parameters"
        raise NotImplementedError()

    def get_exec_annotation(self, execution: TicketExecInfo) -> Dict[str, str]:
        "generate execution metadata"
        raise NotImplementedError()

    def get_exec_result(self, execution_annotation: Dict[str, str]) -> (Optional[TicketExecResultInfo], str):
        "get execution details with annotation metadata"
        raise NotImplementedError()

    def get_exec_log(self, log_query_args: Dict[str, str]) -> TicketTaskLog:
        "get exec log by query args"
        raise NotImplementedError()
