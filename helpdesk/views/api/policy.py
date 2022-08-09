from typing import List, Optional
from datetime import datetime
from fastapi import HTTPException, Depends
from fastapi_pagination import Page, Params, paginate
from helpdesk.models.db.policy import Policy, TicketPolicy, GroupUser
from helpdesk.models.user import User
from helpdesk.libs.dependency import get_current_user, require_admin
from helpdesk.models.action_tree import action_tree
from . import router
from .schemas import PolicyFlowReq, PolicyFlowResp, TicketPolicyReq, TicketPolicyResp, ConfigType, GroupUserReq, GroupUserResp


@router.get('/policies', response_model=Page[PolicyFlowResp])
async def policy_list(params: Params = Depends(), _: User = Depends(require_admin)):
    policies = await Policy.get_all()
    return paginate(policies, params)


@router.get('/policies/{policy_id}', response_model=PolicyFlowResp)
async def get_policy(policy_id: int, _: User = Depends(require_admin)):
    policy = await Policy.get(policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail="approval flow not found")
    return policy


@router.post('/policies', response_model=PolicyFlowResp)
async def create_policy(flow_data: PolicyFlowReq, current_user: User = Depends(get_current_user),
                        _: User = Depends(require_admin)):
    policy = Policy(
        name=flow_data.name,
        display=flow_data.display,
        definition=flow_data.definition.dict(),
        created_by=current_user.name,
        created_at=datetime.now(),
        updated_by='',
        updated_at=datetime.now())
    policy_id = await policy.save()
    new_policy = await Policy.get(policy_id)
    if not new_policy:
        raise HTTPException(status_code=500, detail="policy create failed")
    return new_policy


@router.put('/policies/{policy_id}', response_model=PolicyFlowResp)
async def update_policy(policy_id: int, flow_data: PolicyFlowReq, current_user: User = Depends(get_current_user), _: User = Depends(require_admin)):
    policy = await Policy.get(policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail="approval flow not found")
    policy_form = flow_data.dict()
    policy_form["updated_by"] = current_user.name
    policy_form["updated_at"] = datetime.now()
    await policy.update(**policy_form)
    update_data = await Policy.get(policy_id)
    return update_data


@router.delete('/policies/{policy_id}')
async def remove_policy(policy_id: int, _: User = Depends(require_admin)):
    policy = await Policy.get(policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail="approval flow not found")
    return await Policy.delete(policy_id)


@router.get('/associates', response_model=List[TicketPolicyResp])
async def get_policy_associate(config_type: ConfigType, policy_id: Optional[int] = 0, target_object: Optional[str] = "", _: User = Depends(require_admin)):
    if config_type == ConfigType.policy:
        associates = await TicketPolicy.get_by_policy_id(policy_id)
        return associates
    if config_type == ConfigType.ticket:
        action_tree_leaf = action_tree.find(target_object) if target_object != '' else action_tree.first()
        if not action_tree_leaf:
            raise HTTPException(status_code=404, detail='Target object not found')
        action = action_tree_leaf.action
        associates = await TicketPolicy.get_by_ticket_name(action.target_object)
        return associates


@router.post('/associates', response_model=TicketPolicyResp)
async def add_associate(params: TicketPolicyReq, _: User = Depends(require_admin)):
    ticket_policy_form = TicketPolicy(
        policy_id=params.policy_id,
        ticket_name=params.ticket_name,
        link_condition=params.link_condition
    )
    ticket_policy_id = await ticket_policy_form.save()
    ticket_policy = await TicketPolicy.get(ticket_policy_id)
    if not ticket_policy:
        raise HTTPException(status_code=500, detail="add ticket policy associate failed")
    return ticket_policy


@router.put('/associates/{id}', response_model=TicketPolicyResp)
async def update_associate(id: int, params: TicketPolicyReq, _: User = Depends(require_admin)):
    associate = await TicketPolicy.get(id)
    if not associate:
        raise HTTPException(status_code=404, detail='ticket and policy associate not found')
    ticket_policy_form = params.dict()
    await associate.update(**ticket_policy_form)
    ticket_policy = await TicketPolicy.get(id)
    if not ticket_policy:
        raise HTTPException(status_code=500, detail="ticket policy associate failed")
    return ticket_policy


@router.delete('/associates/{id}')
async def delete_associate(id: int, _: User = Depends(require_admin)):
    associate = await TicketPolicy.get(id)
    if not associate:
        raise HTTPException(status_code=404, detail='ticket and policy associate not found')
    return await TicketPolicy.delete(id)


@router.get('/group_users', response_model=List[GroupUserResp])
async def group_users(_: User = Depends(require_admin)):
    return await GroupUser.get_all()


@router.post('/group_users', response_model=GroupUserResp)
async def add_group_users(params: GroupUserReq, _: User = Depends(require_admin)):
    group_user_form = GroupUser(
        group_name=params.group_name,
        user_str=params.user_str,
    )
    group_user_id = await group_user_form.save()
    group_user = await GroupUser.get(group_user_id)
    if not group_user:
        raise HTTPException(status_code=500, detail="add user group failed")
    return group_user


@router.put('/group_users/{id}', response_model=GroupUserResp)
async def update_group_users(id: int, params: GroupUserReq, _: User = Depends(require_admin)):
    group_user = await GroupUser.get(id)
    if not group_user:
        raise HTTPException(status_code=404, detail='user group not found')
    group_user_form = params.dict()
    await group_user.update(**group_user_form)
    updated_group = await GroupUser.get(id)
    if not updated_group:
        raise HTTPException(status_code=500, detail="user group update failed")
    return updated_group


@router.delete('/group_users/{id}')
async def delete_group_user(id: int, _: User = Depends(require_admin)):
    group_user = await GroupUser.get(id)
    if not group_user:
        raise HTTPException(status_code=404, detail="user group not found")
    return await GroupUser.delete(id)
