import pytest
from httpx import AsyncClient
from backend import schemas

pytestmark = pytest.mark.asyncio

async def test_read_users_me_success(client: AsyncClient, authenticated_user_token: str):
    headers = {"Authorization": f"Bearer {authenticated_user_token}"}
    response = await client.get("/api/users/current", headers=headers)
    assert response.status_code == 200
    user = schemas.User(**response.json()) # Validate against Pydantic schema
    assert user.email == "testuser_functional@example.com" # Email from authenticated_user_token fixture

async def test_read_users_me_unauthenticated(client: AsyncClient):
    response = await client.get("/api/users/current")
    assert response.status_code == 401 # Expecting 401 if not authenticated
    assert "Not authenticated" in response.json()["detail"] # Or "Could not validate credentials"

async def test_update_users_me_success(client: AsyncClient, authenticated_user_token: str):
    headers = {"Authorization": f"Bearer {authenticated_user_token}"}
    update_data = {"name": "Updated Test User Name", "phoneNumber": "0987654321"}
    response = await client.put("/api/users/current", json=update_data, headers=headers)
    assert response.status_code == 200
    user = schemas.User(**response.json())
    assert user.name == update_data["name"]
    assert user.phoneNumber == update_data["phoneNumber"]
    assert user.email == "testuser_functional@example.com" # Email should remain unchanged unless updated

async def test_update_users_me_unauthenticated(client: AsyncClient):
    update_data = {"name": "Attempted Update"}
    response = await client.put("/api/users/current", json=update_data)
    assert response.status_code == 401
