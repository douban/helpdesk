import datetime
from unittest.mock import Mock
import pytest
from httpx import AsyncClient
from pytest import MonkeyPatch
from helpdesk import config
from helpdesk.libs.auth import Validator
from helpdesk.models.action import Action
from helpdesk.models.db import Base
from helpdesk.models.db.ticket import Ticket
from helpdesk.models.provider.airflow import AirflowProvider
from helpdesk.views.api import policy
from helpdesk.models.user import User
from helpdesk.models.action_tree import action_tree
from helpdesk.views.api.schemas import ApproverType, GroupUserReq, Node, NodeDefinition, NodeType, PolicyFlowReq, TicketPolicyReq


@pytest.fixture(autouse=True)
def test_configs():
    SUBTREE = ['账号',
    [['申请账号', '申请账号', 'airflow', 'account_action'],]
    ]
    config.ACTION_TREE_CONFIG = ['功能导航', [SUBTREE]]


@pytest.fixture
def test_admin_user():
    return User(name='admin_user', email='admin_user@douban.com', roles=["admin"])


@pytest.fixture
def test_nomal_user():
    return User(name='test_user', email='test_user@douban.com', roles=[])


@pytest.fixture(autouse=True)
def fake_login(monkeypatch: MonkeyPatch):
    def mock_fetch(_):
        pass
    monkeypatch.setattr(Validator, 'fetch_jwk', mock_fetch)

    from helpdesk import app
    from helpdesk.libs.dependency import get_current_user

    def moke_admin_uer():
        return User(name='admin_user', email='admin_user@douban.com', roles=["admin"])

    app.dependency_overrides[get_current_user] = moke_admin_uer


@pytest.fixture()
def fake_nomal_login(monkeypatch: MonkeyPatch):
    def mock_fetch(_):
        pass
    monkeypatch.setattr(Validator, 'fetch_jwk', mock_fetch)

    from helpdesk import app
    from helpdesk.libs.dependency import get_current_user

    def moke_normal_uer():
        return User(name='test_user', email='test_user@douban.com', roles=[])

    app.dependency_overrides[get_current_user] = moke_normal_uer


@pytest.fixture(autouse=True)
def clean_test_db():
    from helpdesk.libs.db import engine
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
async def test_client():
    from helpdesk import app, config
    async with AsyncClient(app=app, base_url="http://test", headers={"host": config.TRUSTED_HOSTS[0]}) as test_client:
        print("Client is ready")
        yield test_client



@pytest.fixture
async def test_group():
    group_config = await policy.add_group_users(params=GroupUserReq(
        group_name="test_group",
        user_str="test_user"
    ))
    yield group_config


@pytest.fixture
def test_action():
    return Action(name="申请账号", desc="申请账号", provider_object="account_action", provider_name="airflow")


@pytest.fixture
def mock_provider_action(monkeypatch: MonkeyPatch):
    mock_action = {
        'name': "account_action",
        'parameters': {
            "app": {"description": "应用名称", "required": False, "type": "string" }, 
            "department": {"description": "部门名称", "required": False, "type": "string" }, 
            "helpdesk_ticket_callback_url": { "immutable": True, "required": False, "type": "string" }, 
            "ldap_id": { "immutable": True, "required": True, "type": "string" }, 
            "reason": { "description": "申请理由", "required": False, "type": "string" }, 
            "role": { "description": "账号角色类型", "enum": [ "admin", "normal" ], "required": False, "type": "string" } 
        },
    }
    mock_get_action = Mock(return_value=mock_action)
    monkeypatch.setattr(AirflowProvider, "get_action", mock_get_action)


@pytest.fixture
async def test_policy(test_admin_user, test_action):
    policy_config = await policy.create_policy(flow_data=PolicyFlowReq(
        name="test_policy",
        display="test",
        definition=NodeDefinition(nodes=[Node(name="test_node", approvers="test_user", approver_type=ApproverType.PEOPLE, node_type=NodeType.APPROVAL)])
    ), current_user=test_admin_user)
    await policy.add_associate(params=TicketPolicyReq(
        ticket_name=test_action.target_object,
        policy_id=policy_config.id,
        link_condition='["=", 1, 1]',
    ))
    yield policy_config


@pytest.fixture
async def test_cc_submitter_policy(test_admin_user, test_action):
    policy_config = await policy.create_policy(flow_data=PolicyFlowReq(
        name="test_cc_policy_to_submitter",
        display="test",
        definition=NodeDefinition(nodes=[Node(name="test_cc_node", approvers="", approver_type=ApproverType.PEOPLE, node_type=NodeType.CC)])
    ), current_user=test_admin_user)
    await policy.add_associate(params=TicketPolicyReq(
        ticket_name=test_action.target_object,
        policy_id=policy_config.id,
        link_condition=f'["=", "reason", "test_cc_policy_to_submitter"]',
    ))
    yield policy_config


@pytest.fixture
async def test_cc_others_policy(test_admin_user, test_action):
    policy_config = await policy.create_policy(flow_data=PolicyFlowReq(
        name="test_cc_policy_to_others",
        display="test",
        definition=NodeDefinition(nodes=[Node(name="test_cc_node", approvers="test_user", approver_type=ApproverType.PEOPLE, node_type=NodeType.CC)])
    ), current_user=test_admin_user)
    await policy.add_associate(params=TicketPolicyReq(
        ticket_name=test_action.target_object,
        policy_id=policy_config.id,
        link_condition=f'["=", "reason", "test_cc_policy_to_others"]',
    ))
    yield policy_config
