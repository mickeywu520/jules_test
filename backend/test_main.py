import pytest
from httpx import AsyncClient, ASGITransport
from main import app # Import the FastAPI app from main.py

# Mark all tests in this module as async
# This allows using 'async def' for test functions and 'await' for async calls
pytestmark = pytest.mark.asyncio

async def test_read_root():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the FastAPI backend!"}

async def test_get_data():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/data")
    assert response.status_code == 200
    assert response.json() == {"sample_data": ["value1", "value2", "value3"], "status": "success"}

# To run these tests (from the 'backend' directory):
# Ensure your FastAPI app can be imported (e.g., main.py is in the same dir orPYTHONPATH is set)
# Command: python3 -m pytest
