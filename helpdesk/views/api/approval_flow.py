import logging
from datetime import datetime
from fastapi import HTTPException, Depends, Request
from fastapi_pagination import Page, Params, paginate
from helpdesk.models.db.approval_flow import Policy
from helpdesk.models.user import User
from helpdesk.libs.dependency import get_current_user, require_admin

from . import router
from .schemas import PolicyFlowReq, PolicyFlowResp


@router.get('/approval_flows', response_model=Page[PolicyFlowResp])
async def approval_flow_list(params: Params = Depends(), _: User = Depends(require_admin)):
    policys = await Policy.get_all()
    return paginate(policys, params)


@router.post('/approval_flows')
async def add_approval_flow(flow_data: PolicyFlowReq, current_user: User = Depends(get_current_user),
                            _: User = Depends(require_admin)):
    flow = Policy(
        name=flow_data.name,
        display=flow_data.display,
        definition=flow_data.definition,
        created_by=current_user.name,
        created_at=datetime.now(),
        updated_by='',
        updated_at=datetime.now())
    approval_flow_id = await flow.save()
    approval_flow = await Policy.get(approval_flow_id)
    if not approval_flow:
        raise HTTPException(status_code=500, detail="approval flow create failed")
    return dict(
        approval_flows=[approval_flow],
        total=1,
    )


@router.get('/approval_flows/{policy_id}')
@router.patch('/approval_flows/{policy_id}')
async def update_approval_flow(policy_id: int, flow_data: PolicyFlowReq,  request: Request,
                               current_user: User = Depends(get_current_user), _: User = Depends(require_admin)):
    approval_flow = await Policy.get(policy_id)
    if not approval_flow:
        raise HTTPException(status_code=500, detail="approval flow not exist")
    if request.method == 'GET':
        return dict(
            approval_flow=[approval_flow],
            total=1,
        )
    else:
        flow = dict(
            id=policy_id,
            name=flow_data.name if flow_data.name else approval_flow.name,
            display=flow_data.display if flow_data.display else approval_flow.display,
            definition=flow_data.definition if flow_data.definition else approval_flow.definition,
            updated_by=current_user.name,
            updated_at=datetime.now(),
        )
        updated_id = await approval_flow.update(**flow)
        update_policy = await Policy.get(updated_id)
        return dict(
            approval_flows=[update_policy],
            total=1,
        )


@router.delete('/approval_flows/{policy_id}')
async def remove_approval_flow(policy_id: int, _: User = Depends(require_admin)):
    approval_flow = await Policy.get(policy_id)
    if not approval_flow:
        raise HTTPException(status_code=500, detail="approval flow not exist")
    delete_id = await Policy.delete(policy_id)
    return dict(policy_id=delete_id)
