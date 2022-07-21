"""
这个文件里是 pandatic 的 model, 用来构建 fastapi 的请求和响应的body
"""
from enum import Enum
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class MarkTickets(BaseModel):
    """
    标记工单的请求体
    """
    execution_status: str


class ParamRule(BaseModel):
    id: Optional[int]
    title: Optional[str]
    provider_object: Optional[str]
    rule: Optional[str]
    is_auto_approval: Optional[bool]
    approver: Optional[str]


class OperateTicket(BaseModel):
    """
    操作工单的请求体
    """
    reason: Optional[str]


class PolicyFlowResp(BaseModel):
    """
    审批流的响应体
    """
    id: int
    name: Optional[str]
    display: str
    definition: Optional[dict]

    created_at: datetime
    created_by: Optional[str]
    updated_at: datetime
    updated_by: Optional[str]

    class Config:
        orm_mode = True


class Node(BaseModel):
    """
    审批流的节点定义
    approvers: "aaa,bbb,ccc"
    """
    name: Optional[str]
    desc: Optional[str]
    approvers: Optional[str]
    next: Optional[str] = ""


class PolicyFlowReq(BaseModel):
    """
    审批流的请求体
    """
    name: str
    display: str = ""
    definition: Optional[dict]


class TicketPolicyReq(BaseModel):
    """
    工单和审批流关联的请求体
    """
    ticket_name: str
    policy_id: int
    link_condition: str
    

class TicketPolicyResp(BaseModel):
    """
    工单和审批流关联的响应体
    """
    id: int
    ticket_name: Optional[str]
    policy_id: Optional[int]
    link_condition: Optional[str]

    class Config:
        orm_mode = True


class NotifyMessage(BaseModel):
    """
    notify message
    """
    phase: str
    title: str
    ticket_url: str
    status: str
    is_approved: bool
    submitter: str
    params: Dict[str, str]
    request_time: datetime
    reason: str = ""
    approval_flow: str = ""
    current_node: str = ""
    approvers: str = ""
    next_node: Optional[str] = ""
    approval_log: List[Dict] = []


class ConfigType(Enum):
    ticket = "ticket"
    policy = "policy"
