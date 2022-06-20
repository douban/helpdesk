"""
这个文件里是 pandatic 的 model, 用来构建 fastapi 的请求和响应的body
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


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


class PolicyFlow(BaseModel):
    """
    审批流
    """
    id: int
    name: Optional[str]
    display: Optional[str]
    definition: Optional[str]

    created_at: datetime
    created_by:Optional[str]
    update_at: datetime = None
    updated_by:Optional[str]
