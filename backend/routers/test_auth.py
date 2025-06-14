import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session
from backend import models, schemas # For type hinting and checking response models

pytestmark = pytest.mark.asyncio

# Test User Registration
async def test_register_user_success(client: AsyncClient, db_session: Session):
    user_data = {
        "email": "newuser@example.com",
        "password": "newpassword123",
        "name": "New User",
        "phoneNumber": "1234567890",
        "role": "USER" # Assuming UserRole.USER from schemas/models
    }
    response = await client.post("/api/auth/register", json=user_data)
    assert response.status_code == 200 # Should be 200 based on current auth.py, or 201 if changed
    data = response.json()
    assert data["email"] == user_data["email"]
    assert "id" in data
    # Check user in DB
    user_in_db = db_session.query(models.User).filter(models.User.email == user_data["email"]).first()
    assert user_in_db is not None
    assert user_in_db.name == user_data["name"]

async def test_register_user_duplicate_email(client: AsyncClient, authenticated_user_token: str, db_session: Session):
    # The authenticated_user_token fixture has already created "testuser_functional@example.com"
    # and it's available in the db_session for this test function.
    user_data_duplicate = {
        "email": "testuser_functional@example.com", # Attempt to register the same email
        "password": "anotherpassword",
        "name": "Another Test User Functional"
    }
    response = await client.post("/api/auth/register", json=user_data_duplicate)
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]

# Test User Login
async def test_login_success(client: AsyncClient, authenticated_user_token: str): # Fixture creates user and logs in
    # The fixture itself tests login. We just check token presence.
    assert authenticated_user_token is not None

async def test_login_incorrect_email(client: AsyncClient):
    login_data = {"username": "wronguser@example.com", "password": "testpassword"}
    response = await client.post("/api/auth/login", data=login_data)
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]

async def test_login_incorrect_password(client: AsyncClient, db_session: Session):
    # Create a user first if not using the fixture that does it
    from backend.security import get_password_hash
    email = "loginfail@example.com"
    hashed_password = get_password_hash("correctpassword")
    user = models.User(email=email, password=hashed_password, name="Login Fail User")
    db_session.add(user)
    db_session.commit()

    login_data = {"username": email, "password": "wrongpassword"}
    response = await client.post("/api/auth/login", data=login_data)
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]
