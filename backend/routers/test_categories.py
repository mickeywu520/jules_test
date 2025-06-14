import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session
from backend import models, schemas

pytestmark = pytest.mark.asyncio

async def test_create_category_success(client: AsyncClient, authenticated_user_token: str, db_session: Session):
    headers = {"Authorization": f"Bearer {authenticated_user_token}"}
    category_data = {"name": "Electronics"}
    response = await client.post("/api/categories/add", json=category_data, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == category_data["name"]
    assert "id" in data
    # Check in DB
    category_in_db = db_session.query(models.Category).filter(models.Category.name == category_data["name"]).first()
    assert category_in_db is not None

async def test_create_category_duplicate_name(client: AsyncClient, authenticated_user_token: str):
    headers = {"Authorization": f"Bearer {authenticated_user_token}"}
    category_data = {"name": "Books"}
    # Create first time
    response1 = await client.post("/api/categories/add", json=category_data, headers=headers)
    assert response1.status_code == 201
    # Attempt to create again
    response2 = await client.post("/api/categories/add", json=category_data, headers=headers)
    assert response2.status_code == 400
    assert "already exists" in response2.json()["detail"]

async def test_read_categories_success(client: AsyncClient, authenticated_user_token: str, db_session: Session):
    headers = {"Authorization": f"Bearer {authenticated_user_token}"}
    # Create a category first
    db_session.add(models.Category(name="Test Category For Read"))
    db_session.commit()

    response = await client.get("/api/categories/all", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0 # Assuming the one we created is there
    assert any(c["name"] == "Test Category For Read" for c in data)

async def test_read_specific_category_success(client: AsyncClient, authenticated_user_token: str, db_session: Session):
    headers = {"Authorization": f"Bearer {authenticated_user_token}"}
    category = models.Category(name="Specific Category")
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category) # To get ID

    response = await client.get(f"/api/categories/{category.id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == category.name
    assert data["id"] == category.id

async def test_read_specific_category_not_found(client: AsyncClient, authenticated_user_token: str):
    headers = {"Authorization": f"Bearer {authenticated_user_token}"}
    response = await client.get("/api/categories/99999", headers=headers) # Non-existent ID
    assert response.status_code == 404

async def test_update_category_success(client: AsyncClient, authenticated_user_token: str, db_session: Session):
    headers = {"Authorization": f"Bearer {authenticated_user_token}"}
    category = models.Category(name="Original Category Name")
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)

    update_data = {"name": "Updated Category Name"}
    response = await client.put(f"/api/categories/update/{category.id}", json=update_data, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]
    # Verify in DB
    db_session.expire_all() # Expire cache to ensure fresh read
    updated_category_in_db = db_session.query(models.Category).filter(models.Category.id == category.id).first()
    assert updated_category_in_db is not None # Ensure it still exists
    assert updated_category_in_db.name == update_data["name"]

async def test_update_category_not_found(client: AsyncClient, authenticated_user_token: str):
    headers = {"Authorization": f"Bearer {authenticated_user_token}"}
    update_data = {"name": "Non Existent Update"}
    response = await client.put("/api/categories/update/88888", json=update_data, headers=headers)
    assert response.status_code == 404

async def test_delete_category_success(client: AsyncClient, authenticated_user_token: str, db_session: Session):
    headers = {"Authorization": f"Bearer {authenticated_user_token}"}
    category = models.Category(name="Category To Delete")
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)

    response = await client.delete(f"/api/categories/delete/{category.id}", headers=headers)
    assert response.status_code == 200 # Assuming it returns the deleted object
    # Verify not in DB
    deleted_category_in_db = db_session.query(models.Category).filter(models.Category.id == category.id).first()
    assert deleted_category_in_db is None

async def test_delete_category_not_found(client: AsyncClient, authenticated_user_token: str):
    headers = {"Authorization": f"Bearer {authenticated_user_token}"}
    response = await client.delete("/api/categories/delete/77777", headers=headers)
    assert response.status_code == 404

async def test_delete_category_with_products_forbidden(client: AsyncClient, authenticated_user_token: str, db_session: Session):
    headers = {"Authorization": f"Bearer {authenticated_user_token}"}
    # Create category
    category_with_prod = models.Category(name="Category With Product")
    db_session.add(category_with_prod)
    db_session.commit()
    db_session.refresh(category_with_prod)
    # Create product associated with this category
    product = models.Product(name="Test Product", price=10.0, category_id=category_with_prod.id)
    db_session.add(product)
    db_session.commit()

    response = await client.delete(f"/api/categories/delete/{category_with_prod.id}", headers=headers)
    assert response.status_code == 400 # Forbidden due to associated products
    assert "Cannot delete category with associated products" in response.json()["detail"]
