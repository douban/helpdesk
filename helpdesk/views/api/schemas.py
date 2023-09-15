"""
这个文件里是 pandatic 的 model, 用来构建 fastapi 的请求和响应的body
"""
from enum import Enum
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class MarkTickets(BaseModel):
    """
    标记工单的请求体
    """
    execution_status: str


class QeuryKey(str, Enum):
    """
    ticket支持模糊匹配的key
    """
    TITLE = 'title__icontains'
    PARAMS = 'params__icontains'
    REASON = 'reason__icontains'
    SUBMMITER = 'submitter__icontains'
    CONFIRMED_BY = 'confirmed_by__icontains'


class ParamRule(BaseModel):
    id: Optional[int] = None
    title: Optional[str] = None
    provider_object: Optional[str] = None
    rule: Optional[str] = None
    is_auto_approval: Optional[bool] = None
    approver: Optional[str] = None


class OperateTicket(BaseModel):
    """
    操作工单的请求体
    """
    reason: Optional[str] = None


class PolicyFlowResp(BaseModel):
    """
    审批流的响应体
    """
    id: int
    name: str
    display: str
    definition: Optional[dict]

    created_at: datetime
    created_by: Optional[str]
    updated_at: datetime
    updated_by: Optional[str]

    class Config:
        orm_mode = True


class NodeType(str, Enum):
    """
    节点类型 cc 则自动同意,抄送给approver; approval 则需要审批
    """
    CC = 'cc'
    APPROVAL = 'approval'


class ApproverType(str, Enum):
    """
    审批人类型
    app_owner: dae 应用 owner
    group: 用户组
    people: 指定人
    """
    APP_OWNER = "app_owner"
    GROUP = "group"
    PEOPLE = "people"
    DEPARTMENT = "department"


class Node(BaseModel):
    """
    审批流的节点定义
    approvers: "aaa,bbb,ccc", 如果是通讯组之类的则也可多个通讯组拼接str
    节点顺序根据列表的先后顺序来
    """
    name: str
    approvers: str
    approver_type: ApproverType = ApproverType.PEOPLE
    node_type: NodeType = NodeType.APPROVAL


class NodeDefinition(BaseModel):
    version: str = "0.1"
    nodes: List[Node]


class PolicyFlowReq(BaseModel):
    """
    审批流的请求体
    """
    name: str
    display: str = ""
    definition: NodeDefinition


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
    params: dict
    request_time: datetime
    reason: str = ""
    approval_flow: str = ""
    current_node: str = ""
    approvers: str = ""
    next_node: Optional[str] = ""
    approval_log: List[dict] = []
    notify_type: str
    notify_people: str = ""
    comfirmed_by: str = ""


class ConfigType(Enum):
    ticket = "ticket"
    policy = "policy"


class GroupUserReq(BaseModel):
    """
    用户组的请求体
    """
    group_name: str
    user_str: str
    

class GroupUserResp(BaseModel):
    """
    用户组的响应体
    """
    id: int
    group_name: str
    user_str: str

    class Config:
        orm_mode = True
