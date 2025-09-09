from enum import Enum
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime

from pydantic import BaseModel


class ParamType(Enum):
    STRING = "string"
    BOOL = "boolean"
    INTEGER = "integer"


class RunnerType(Enum):
    AIRFLOW = "airflow"
    SPINCYCLE = "spincycle"


class StatusColor(Enum):
    SUCCESS = 'green'
    RUNNING = '#00ff00'
    SKIPPED = '#fecfd7'
    UPSTREAM_FAILED = '#feba3f'
    UP_FOR_RESCHEDULE = '#6fe7db'
    UP_FOR_RETRY = '#fee03f'
    QUEUED = '#808080'
    NO_STATUS = '#fafafa'


class StatusEmoji(Enum):
    SUCCESS = '✅'
    RUNNING = '🏃'
    FAILED = '❌'
    SKIPPED = '👉'
    UPSTREAM_FAILED = '🔺'
    UP_FOR_RESCHEDULE = '🔁'
    UP_FOR_RETRY = '🔄'
    QUEUED = '🫸'
    NO_STATUS = '🤌'


class Param(BaseModel):
    description: Optional[str]
    type: ParamType
    enum: Optional[List[str | int | float]] = None
    required: bool = False
    immutable: bool = False
    default: Optional[str] = None


class FormParams(BaseModel):
    params_def: Dict[str, Param]
    json_schema: Dict[str, Any]


class ActionInfo(BaseModel):
    name: str
    description: str
    action_id: str


class ActionSchema(BaseModel):
    id: str
    name: str
    parameters: Dict[str, Param]
    tags: List[str]
    description: str
    params_json_schema: Dict[str, Any]
    pack: str
    runner_type: RunnerType
    highlight_queries: Optional[str] = None
    pretty_log_formatter: Optional[Dict[str, Any]] = None
    status_filter: Optional[Tuple[str]] = None


class TicketExecInfo(BaseModel):
    exec_id: str
    execution_date: datetime
    msg: str
    ticket_name: str
    runner: RunnerType
    web_url: Optional[str] = None


class TicketExecTaskStatus(Enum):
    REMOVED = 'removed'
    SCHEDULED = 'scheduled'
    QUEUED = 'queued'
    RUNNING = 'running'
    SUCCESS = 'success'
    RESTARTING = 'restarting'
    FAILED = 'failed'
    UP_FOR_RETRY = 'up_for_retry'
    UP_FOR_RESCHEDULE = 'up_for_reschedule'
    UPSTREAM_FAILED = 'upstream_failed'
    SKIPPED = 'skipped'
    DEFERRED = 'deferred'
    NO_STATUS = 'no_status'


class TicketExecStatus(Enum):
    SUCCESS = "success"
    RUNNING = "running"
    FAILED = "failed"
    NO_STATUS = "no_status"
    QUEUED = "queued"


class TicketExecTaskDetails(BaseModel):
    status: TicketExecTaskStatus
    failed: bool
    stderr: str
    return_code: int
    succeeded: bool
    stdout: str
    highlight_queries: str


class TicketExecTaskInfo(BaseModel):
    name: str
    execution_id: str
    task_id: str
    created_at: datetime = None
    updated_at: datetime = None
    state: TicketExecTaskStatus = TicketExecTaskStatus.NO_STATUS
    # 结果包含多次retry
    result: Dict[str, TicketExecTaskDetails] = None


class TicketExecTasksResult(BaseModel):
    tasks: List[TicketExecTaskInfo]
    id: str


class TicketGraphNode(BaseModel):
    key: str
    text: str
    color: StatusColor = StatusColor.NO_STATUS
    stroke: StatusColor = StatusColor.NO_STATUS


class TicketGraphLink(BaseModel):
    to: str
    from_: str


class TicketGraph(BaseModel):
    class_: str = "GraphLinksModel"
    nodes: List[TicketGraphNode] = None
    edges: List[TicketGraphLink] = None


class TicketExecResultInfo(BaseModel):
    ticket_id: str
    status: TicketExecStatus
    start_timestamp: datetime
    web_url: str
    result: TicketExecTasksResult
    graph: TicketGraph


class TicketTaskLog(BaseModel):
    message: str
    load_success: bool = False
    pretrty_log: Optional[str] = None
