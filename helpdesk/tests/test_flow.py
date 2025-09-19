from datetime import datetime
import pytest
from helpdesk.models.db.ticket import Ticket, TicketPhase
from helpdesk.libs.notification import MailNotification, WebhookEventNotification
from helpdesk.views.api.schemas import NodeType


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
        reason=params.get("reason"),
        created_at=datetime.now(),
    )
    policy = await ticket.get_flow_policy()
    assert policy == None


@pytest.mark.anyio
@pytest.mark.parametrize(
    "params, policy_name, approvers, can_view",
    [
        pytest.param({}, "test_policy", "test_user", True),
        pytest.param(
            {
                "reason": "test_cc_policy_to_submitter",
            },
            "test_cc_policy_to_submitter",
            "",
            False,
        ),
        pytest.param(
            {"reason": "test_cc_policy_to_others"},
            "test_cc_policy_to_others",
            "test_user",
            True,
        ),
        pytest.param(
            {"reason": "test_approval_policy_by_group"},
            "test_approval_policy_by_group",
            "test_user",
            True,
        ),
        # pytest.param({"reason": "test_approval_policy_by_app", "app": "test_app"}, "test_approval_policy_by_app", "", False),
        pytest.param(
            {
                "reason": "test_approval_policy_by_department",
                "department": "test_department",
            },
            "test_approval_policy_by_department",
            "department_user",
            False,
        ),
        pytest.param(
            {"reason": "test_combined_policy"},
            "test_combined_policy",
            "admin_user, normal_user",
            True,
        ),
    ],
)
async def test_flow_match(
    test_action,
    test_admin_user,
    params,
    policy_name,
    approvers,
    can_view,
    test_all_policy,
    test_user,
):
    # 测试ticket和policy的匹配 - 默认审批流
    ticket = Ticket(
        title="test",
        provider_type=test_action.provider_type,
        provider_object=test_action.target_object,
        params=params,
        extra_params={},
        submitter=test_admin_user.name,
        reason=params.get("reason"),
        created_at=datetime.now(),
    )
    policy = await ticket.get_flow_policy()
    assert policy.name == policy_name
    # 测试节点 approver 获取
    ticket.annotate(
        nodes=policy.definition.get("nodes") or [],
        policy=policy.name,
        approval_log=list(),
    )
    current_node = ticket.init_node.get("name")
    ticket.annotate(current_node=current_node)
    node_approvers = await ticket.get_node_approvers(current_node)
    assert node_approvers == approvers
    # 测试能看到 ticket 的用户
    assert await ticket.can_view(test_user) == can_view


@pytest.mark.anyio
@pytest.mark.parametrize(
    "phase, params, mail_approvers, notify_approvers, notify_type, notify_people",
    [
        pytest.param(
            TicketPhase.REQUEST,
            {},
            "test_user",
            "test_user",
            NodeType.APPROVAL,
            "test_user",
        ),
        pytest.param(
            TicketPhase.APPROVAL,
            {},
            "test_user,admin_user@example.com",
            "",
            NodeType.CC,
            "test_user,admin_user",
        ),
        pytest.param(
            TicketPhase.MARK,
            {},
            "test_user,admin_user@example.com",
            "",
            NodeType.CC,
            "admin_user",
        ),
        pytest.param(
            TicketPhase.REQUEST,
            {"reason": "test_cc_policy_to_submitter"},
            "",
            "",
            NodeType.CC,
            "admin_user",
        ),
    ],
)
async def test_mail_notify(
    test_action,
    test_admin_user,
    test_all_policy,
    phase,
    params,
    mail_approvers,
    notify_approvers,
    notify_type,
    notify_people,
):
    # 测试通知
    ticket = Ticket(
        title="test",
        provider_type=test_action.provider_type,
        provider_object=test_action.target_object,
        params=params,
        extra_params={},
        submitter=test_admin_user.name,
        reason=params.get("reason"),
        created_at=datetime.now(),
    )
    policy = await ticket.get_flow_policy()
    ticket.annotate(
        nodes=policy.definition.get("nodes") or [],
        policy=policy.name,
        approval_log=list(),
    )
    current_node = ticket.init_node.get("name")
    ticket.annotate(current_node=current_node)
    approvers = await ticket.get_node_approvers(current_node)
    ticket.annotate(approvers=approvers)
    mail_notify = MailNotification(phase, ticket)
    mail_addrs = await mail_notify.get_mail_addrs()
    assert mail_addrs == mail_approvers

    # webhook notify 测试
    webhook_notify = WebhookEventNotification(phase, ticket)
    webhook_message = webhook_notify.render()
    # print(webhook_message)
    assert webhook_message.approvers == notify_approvers
    assert webhook_message.notify_people == notify_people
    assert webhook_message.notify_type == notify_type


@pytest.mark.anyio
async def test_node_transfer(test_action, test_admin_user, test_combined_policy):
    # 测试节点流转
    ticket = Ticket(
        title="test",
        provider_type=test_action.provider_type,
        provider_object=test_action.target_object,
        params={"reason": "test_combined_policy"},
        extra_params={},
        submitter=test_admin_user.name,
        reason="test_combined_policy",
        created_at=datetime.now(),
    )
    policy = await ticket.get_flow_policy()

    ticket.annotate(
        nodes=policy.definition.get("nodes") or [],
        policy=policy.name,
        approval_log=list(),
    )
    current_node = ticket.init_node.get("name")
    ticket.annotate(current_node=current_node)
    ret, msg = await ticket.approve()
    assert ret == True
    assert msg == "Success"
