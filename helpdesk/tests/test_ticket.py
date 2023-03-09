import pytest
from httpx import AsyncClient


def test_admin_panel():
    """
    admin_panel 接口已由 associate 替换
    """
    pass


@pytest.mark.anyio
async def test_action(test_client: AsyncClient, test_action):
    # 获取 action
    action_list = await test_client.get("/api/action_tree")
    assert action_list.status_code == 200
    assert action_list.json()[0].get("name") == "功能导航"
    target_action = await test_client.get(f"/api/action/{test_action.target_object}")
    assert target_action.status_code == 404


@pytest.mark.anyio
async def test_ticket(test_client: AsyncClient, test_action, test_policy):
    list_ticket = await test_client.get("/api/ticket")
    assert list_ticket.status_code == 200
    # create ticket
    create_ticket = await test_client.post(f"/api/action/{test_action.target_object}")
    assert create_ticket.status_code == 404
