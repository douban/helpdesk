from httpx import AsyncClient
import pytest


@pytest.mark.anyio
async def test_index(test_client: AsyncClient):
    response = await test_client.get("/api/")
    assert response.status_code == 200
    assert response.json() == {"msg": "Hello API"}


@pytest.mark.anyio
async def test_user_me(test_client: AsyncClient, test_admin_user):
    response = await test_client.get("/api/user/me")
    assert response.status_code == 200
    assert response.json().get("name") == test_admin_user.name
