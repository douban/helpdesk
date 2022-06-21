import logging
from datetime import datetime
from fastapi import HTTPException, Depends
from fastapi_pagination import Page, Params, paginate
from helpdesk.models.db.policy import Policy, TicketPolicy
from helpdesk.models.user import User
from helpdesk.libs.dependency import get_current_user, require_admin

from . import router
from .schemas import PolicyFlowReq, PolicyFlowResp, TicketPolicyReq


@router.get('/policies', response_model=Page[PolicyFlowResp])
async def policy_list(params: Params = Depends(), _: User = Depends(require_admin)):
    policies = await Policy.get_all()
    return paginate(policies, params)


@router.post('/policies')
async def add_policy(flow_data: PolicyFlowReq, current_user: User = Depends(get_current_user),
                     _: User = Depends(require_admin)):
    policy = Policy(
        name=flow_data.name,
        display=flow_data.display,
        definition=flow_data.definition,
        created_by=current_user.name,
        created_at=datetime.now(),
        updated_by='',
        updated_at=datetime.now())
    policy_id = await policy.save()
    new_policy = await Policy.get(policy_id)
    if not new_policy:
        raise HTTPException(status_code=500, detail="policy create failed")
    return dict(
        policies=[new_policy],
        total=1,
    )


@router.get('/policies/{policy_id}')
async def get_policy(policy_id: int, _: User = Depends(require_admin)):
    policy = await Policy.get(policy_id)
    if not policy:
        raise HTTPException(status_code=500, detail="policy not exist")
    return dict(
        policies=[policy],
        total=1,
    )


@router.patch('/policies/{policy_id}')
async def update_policy(policy_id: int, flow_data: PolicyFlowReq, current_user: User = Depends(get_current_user),
                        _: User = Depends(require_admin)):
    policy = await Policy.get(policy_id)
    if not policy:
        raise HTTPException(status_code=500, detail="policy not exist")

    flow = dict(
        id=policy_id,
        name=flow_data.name if flow_data.name else policy.name,
        display=flow_data.display if flow_data.display else policy.display,
        definition=flow_data.definition if flow_data.definition else policy.definition,
        updated_by=current_user.name,
        updated_at=datetime.now(),
    )
    await policy.update(**flow)
    update_data = await Policy.get(policy_id)
    return dict(
        policies=[update_data],
        total=1,
    )


@router.delete('/policies/{policy_id}')
async def remove_policy(policy_id: int, _: User = Depends(require_admin)):
    policy = await Policy.get(policy_id)
    if not policy:
        raise HTTPException(status_code=500, detail="approval flow not exist")
    await Policy.delete(policy_id)
    return dict(policy_id=policy_id)


@router.post('/policy_associate')
async def ticket_policy_associate(params: TicketPolicyReq, _: User = Depends(require_admin)):
    ticket_policy_form = TicketPolicy(
        policy_id=params.policy_id,
        ticket_name=params.ticket_name,
        link_condition=params.link_condition
    )
    ticket_policy_id = await ticket_policy_form.save()
    ticket_policy = await TicketPolicy.get(ticket_policy_id)
    if not ticket_policy:
        raise HTTPException(status_code=500, detail="ticket policy associate failed")
    return dict(
        association=[ticket_policy],
        total=1,
    )