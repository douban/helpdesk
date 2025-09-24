from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime

from helpdesk.libs.types import (
    TicketExecResultInfo,
    ActionInfo,
    ActionSchema,
    TicketExecInfo,
    TicketTaskLog,
)


class BaseProvider:
    """
    action: capability to execute a series of tasks.
    ticket: an action with specified arguments.
    pack: a collection of actions; the provider needs to provide a way to resolve the action list by pack.
          This serves as an automatic discovery method for tickets. For example, you can map a pack to an Airflow DAG tag.
          If anyone writes a DAG with this tag (pack), the helpdesk will show this DAG as a helpdesk action.
          Pack is defined in action tree config with a dot as postfix.
    action_name: an internal unique identifier for the action; the provider should offer a way to retrieve the schema
          by the action_name.
    ticket_name: same as action_name.
    execution: when the provider receives a ticket submission, it should send the ticket to the actual backend
          and return immediately. The provider should not wait for the ticket execution to complete.
          The provider should save the execution metadata as annotations and wait for the user to request
          the ticket result.

    The provider's call chain is as follows:

    - User requests the action tree list by `get_actions_info`.
    - User selects a ticket by `get_action_schema`.
    - User submits a ticket that has been approved via `exec_ticket`.
    - Provider saves execution metadata using `get_exec_annotation`.
    - User checks the ticket result by `get_exec_result`.
    - User checks task logs using `get_exec_log`.
    """

    provider_type = None

    def __init__(self, **kwargs):
        pass

    def __str__(self):
        attrs = []
        for k in sorted(self.__dict__):
            if k.startswith("_"):
                continue
            v = getattr(self, k)
            v = '"%s"' % str(v) if type(v) in (str, datetime) else str(v)
            attrs.append("%s=%s" % (k, v))
        return "%s(%s)" % (self.__class__.__name__, ", ".join(attrs))

    __repr__ = __str__

    def get_default_pack(self) -> str:
        "provider default pack supported"
        raise NotImplementedError()

    def get_actions_info(self, pack: Optional[str]) -> List[ActionInfo]:
        "get actions simple info"
        raise NotImplementedError()

    def get_action_schema(self, action_name: str) -> Optional[ActionSchema]:
        raise NotImplementedError()

    def exec_ticket(
        self, ticket_name: str, parameters: Dict[str, Any]
    ) -> Tuple[TicketExecInfo, str]:
        "run action with parameters"
        raise NotImplementedError()

    def get_exec_annotation(self, execution: TicketExecInfo) -> Dict[str, Any]:
        "generate execution metadata"
        raise NotImplementedError()

    def get_exec_result(
        self, execution_annotation: Dict[str, Any]
    ) -> (Optional[TicketExecResultInfo], str):
        "get execution details with annotation metadata"
        raise NotImplementedError()

    def get_exec_log(self, log_query_args: Dict[str, str]) -> TicketTaskLog:
        "get exec log by query args"
        raise NotImplementedError()
