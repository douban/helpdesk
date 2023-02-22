from httpx import AsyncClient
import pytest


@pytest.mark.anyio
async def test_policy(test_client: AsyncClient):
    # 审批流CRUD操作
    list_response = await test_client.get("/api/policies")
    assert list_response.status_code == 200
    create_response = await test_client.post("/api/policies", json={"name": "test_policy","display": "","definition": {"version": "0.1","nodes": [{
        "name": "test_node",
        "approvers": "test_user",
        "approver_type": "people",
        "node_type": "approval"
        }]}
    })
    assert create_response.status_code == 200
    policy_id = create_response.json().get("id")
    policy = await test_client.get(f"/api/policies/{policy_id}")
    assert policy.status_code == 200
    assert policy.json().get("name") == "test_policy"
    modify_policy = await test_client.put(f"/api/policies/{policy_id}", json={"name": "test_policy","display": "test_update","definition": {"version": "0.1","nodes": [{
        "name": "test_approve_node",
        "approvers": "test_user",
        "approver_type": "people",
        "node_type": "approval"
        }, {
        "name": "test_cc_node",
        "approvers": "admin_user",
        "approver_type": "people",
        "node_type": "cc"
        }]}
    })
    assert modify_policy.status_code == 200
    assert modify_policy.json().get("display") == "test_update"
    assert len(modify_policy.json().get("definition").get("nodes")) == 2
    delete_policy = await test_client.delete(f"/api/policies/{policy_id}")
    assert delete_policy.status_code == 200
    after_del_policy = await test_client.get(f"/api/policies/{policy_id}")
    assert after_del_policy.status_code == 404


@pytest.mark.anyio
async def test_group_user(test_client: AsyncClient):
    # 用户组CRUD操作
    create_response = await test_client.post("/api/group_users", json={"group_name":"test_group", "user_str":"aaa,bbb,cccc"})
    assert create_response.status_code == 200
    group_id = create_response.json().get("id")
    modify_response = await test_client.put(f"/api/group_users/{group_id}", json={"group_name":"test_group1", "user_str":"test_user"})
    assert modify_response.status_code == 200 
    assert modify_response.json().get("user_str") == "test_user"
    assert modify_response.json().get("group_name") == "test_group1"
    delete_response = await test_client.delete(f"/api/group_users/{group_id}")
    assert delete_response.status_code == 200
    list_response = await test_client.get("/api/group_users")
    assert list_response.status_code == 200


@pytest.mark.anyio
async def test_associates(test_client: AsyncClient, test_policy):
    # policy 和 ticket 的关联CRUD操作
    create_response = await test_client.post("/api/associates", json={"ticket_name":"test_ticket_action", "policy_id":test_policy.id, "link_condition":'["=", 1, 1]'})
    assert create_response.status_code == 200
    assert create_response.json().get("policy_id") == test_policy.id
    associate_id = create_response.json().get("id")
    list_by_ticket = await test_client.get("/api/associates", params={"config_type": "ticket", "ticket_name": "test_ticket_action"})
    assert list_by_ticket.status_code == 200
    modify_response = await test_client.put(f"/api/associates/{associate_id}", json={"ticket_name":"test_ticket_action_modify", "policy_id":test_policy.id, "link_condition":'["=", 1, 1]'})
    assert modify_response.status_code == 200
    assert modify_response.json().get("ticket_name") == "test_ticket_action_modify"
    delete_response = await test_client.delete(f"/api/associates/{associate_id}")
    assert delete_response.status_code == 200
    list_by_policy = await test_client.get("/api/associates", params={"config_type": "policy", "policy_id": test_policy.id})
    assert list_by_policy.status_code == 200
    assert modify_response.json() not in list_by_policy.json()
        



