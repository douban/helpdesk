import logging
from datetime import datetime
from fastapi import Query, HTTPException, Depends, Request
from fastapi_pagination import Page, paginate, add_pagination
from helpdesk.models.db.approval_flow import Policy, policys
from helpdesk.models.user import User
from helpdesk.libs.dependency import get_current_user, require_admin

from . import router
from .schemas import PolicyFlow


@router.get('/approval_flows', response_model=Page[PolicyFlow])
async def approval_flow_list(_: User = Depends(require_admin)):
    return paginate(policys)

add_pagination(router)


@router.get('/approval_flows/{policy_id}')
async def get_approval_flow(policy_id: int, _: User = Depends(require_admin)):
    approval_flow = await Policy.get(policy_id)
    if not approval_flow:
        raise HTTPException(status_code=404, detail="approval flow not found")
    return dict(
        approval_flows=[approval_flow],
        total=1,
    )


@router.post('/approval_flows')
async def add_approval_flow(flow_data: PolicyFlow, current_user: User = Depends(get_current_user)):
    flow = Policy(
        name=flow_data.name,
        display=flow_data.display,
        definition=flow_data.definition,
        created_by=current_user,
        created_at=datetime.now(),
        updated_by='',
        update_at=datetime.now())
    approval_flow_id = await flow.save()
    approval_flow = await Policy.get(approval_flow_id)
    if not approval_flow:
        raise HTTPException(status_code=500, detail="approval flow create failed")
    return dict(
        approval_flows=[approval_flow],
        total=1,
    )


@router.post('/approval_flows/{policy_id}')
async def update_approval_flow(policy_id: int, flow_data: PolicyFlow,  current_user: User = Depends(get_current_user)):
    approval_flow = await Policy.get(policy_id)
    if not approval_flow:
        raise HTTPException(status_code=500, detail="approval flow not exist")
    flow = dict(
        name=flow_data.name,
        display=flow_data.display,
        definition=flow_data.definition,
        updated_by=current_user,
        update_at=datetime.now())
    await approval_flow.update(flow)
    approval_flow = await Policy.get(policy_id)
    return dict(
        approval_flows=[approval_flow],
        total=1,
    )


@router.delete('/approval_flows/{policy_id}')
async def remove_approval_flow(policy_id: int, _: User = Depends(require_admin)):
    approval_flow = await Policy.get(policy_id)
    if not approval_flow:
        raise HTTPException(status_code=500, detail="approval flow not exist")
    delete_id = await Policy.delete(policy_id)
    return dict(data=delete_id)