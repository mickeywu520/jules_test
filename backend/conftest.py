import pytest
import pytest_asyncio # Import for the fixture decorator
from typing import Generator, Any
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport # Import ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Import your FastAPI app and SQLAlchemy Base
from backend.main import app as main_app # Renamed to avoid clash
from backend.database import Base, get_db
from backend.models import User, UserRole # For creating test users and setting role

# --- Test Database Setup (In-memory SQLite) ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"  # In-memory SQLite for testing

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False} # check_same_thread for SQLite
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables in the test database before tests run
Base.metadata.create_all(bind=engine)

# Override the get_db dependency for testing
def override_get_db() -> Generator[Session, Any, None]:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Apply the override to the FastAPI app instance
main_app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def app() -> FastAPI:
    # Re-create tables for each test module if needed, or manage data carefully
    # Base.metadata.drop_all(bind=engine) # Optional: drop tables before creating
    Base.metadata.create_all(bind=engine)
    return main_app

@pytest_asyncio.fixture(scope="module") # Changed to pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncClient:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.fixture(scope="function") # function scope for db session to ensure clean state
def db_session() -> Session:
    # Base.metadata.drop_all(bind=engine) # Clean all data before each test function
    # Base.metadata.create_all(bind=engine) # Recreate tables

    # More granular cleanup: delete data from tables or use transactions
    # For simplicity here, we'll rely on SQLite being in-memory or a fresh file for each run,
    # or careful data management within tests.
    # A better approach for complex tests is transactional tests or deleting specific data.

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        # Clean up: delete all data from tables after each test
        try:
            # Rollback any lingering transaction from the test itself
            db.rollback()
            for table in reversed(Base.metadata.sorted_tables):
                db.execute(table.delete())
            db.commit()
        except Exception as e:
            print(f"Error during DB cleanup: {e}")
            # Optionally re-raise or handle more gracefully
        finally:
            db.close()

# Fixture to create a test user and get an auth token
# This is now function-scoped to align with db_session's cleanup
@pytest_asyncio.fixture(scope="function")
async def authenticated_user_token(client: AsyncClient, db_session: Session): # Depends on function-scoped db_session
    # Create a user directly in the test DB for login
    from backend.security import get_password_hash
    test_user_email = "testuser_functional@example.com" # Use a different email to avoid clashes if module-scoped user still exists somehow
    test_user_password = "testpassword"

    # User should not exist due to function-scoped db_session cleanup
    user = db_session.query(User).filter(User.email == test_user_email).first()
    assert user is None # Ensure user doesn't exist from a previous (failed) run within the same scope if cleanup failed

    hashed_password = get_password_hash(test_user_password)
    user = User(email=test_user_email, password=hashed_password, name="Test User Functional", role=UserRole.USER)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Log in to get token
    login_data = {"username": test_user_email, "password": test_user_password}
    response = await client.post("/api/auth/login", data=login_data)

    if response.status_code != 200:
        pytest.fail(f"Failed to log in test user '{test_user_email}': {response.text} (status code: {response.status_code})")

    token_data = response.json()
    assert "access_token" in token_data
    return token_data["access_token"]
