from datetime import datetime
import pytest
from helpdesk.views.api import policy
from helpdesk.models.db.ticket import Ticket
from helpdesk.models.provider import get_provider
from helpdesk.views.api.schemas import ApproverType, Node, NodeDefinition, NodeType, PolicyFlowReq, TicketPolicyReq


@pytest.mark.anyio
async def test_flow_non_match(test_action, test_admin_user):
    # 测试ticket和policy的不匹配且无默认审批流
    params = {}
    ticket = Ticket(
        title="test",
        provider_type=test_action.provider_type,
        provider_object=test_action.target_object,
        params=params,
        extra_params={},
        submitter=test_admin_user.name,
        reason=params.get('reason'),
        created_at=datetime.now())
    policy = await ticket.get_flow_policy()
    assert policy == None


@pytest.mark.anyio
async def test_flow_match(test_action, test_admin_user, test_policy):
    # 测试ticket和policy的匹配 - 默认审批流
    params = {}
    ticket = Ticket(
        title="test",
        provider_type=test_action.provider_type,
        provider_object=test_action.target_object,
        params=params,
        extra_params={},
        submitter=test_admin_user.name,
        reason=params.get('reason'),
        created_at=datetime.now())
    policy = await ticket.get_flow_policy()
    assert policy.name == "test_policy"


@pytest.mark.anyio
async def test_cc_flow():
    # 审批流只有CC节点(CC-申请人/负责人)
    # provider = get_provider(test_action.provider_type)
    # print(provider)
    # ticket, msg = await test_action.run(provider, {"reason", "test_cc_policy_to_submitter"}, test_admin_user)
    # print(ticket, msg)
    pass



def test_approval_flow():
    # 审批流只有Approval节点(Approval-people/group/app/department)
    pass


def test_multi_node_flow():
    # 多节点审批流
    pass


def notify():
    # 通知审批人
    pass