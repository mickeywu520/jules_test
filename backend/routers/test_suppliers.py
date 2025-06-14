import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session
from backend import models, schemas # For type hinting and checking response models

pytestmark = pytest.mark.asyncio

# --- Supplier Tests ---

async def test_create_supplier_success(client: AsyncClient, authenticated_user_token: str, db_session: Session):
    headers = {"Authorization": f"Bearer {authenticated_user_token}"}
    supplier_data = {
        "name": "Supplier Alpha",
        "contactInfo": "alpha@supplier.com",
        "address": "123 Alpha Street"
    }
    response = await client.post("/api/suppliers/add", json=supplier_data, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == supplier_data["name"]
    assert "id" in data
    supplier_in_db = db_session.query(models.Supplier).filter(models.Supplier.name == supplier_data["name"]).first()
    assert supplier_in_db is not None
    assert supplier_in_db.contactInfo == supplier_data["contactInfo"]

async def test_create_supplier_duplicate_name(client: AsyncClient, authenticated_user_token: str):
    headers = {"Authorization": f"Bearer {authenticated_user_token}"}
    supplier_data = {"name": "Supplier Beta", "contactInfo": "beta@supplier.com"}
    await client.post("/api/suppliers/add", json=supplier_data, headers=headers) # First one
    response = await client.post("/api/suppliers/add", json=supplier_data, headers=headers) # Duplicate
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]

async def test_read_all_suppliers(client: AsyncClient, authenticated_user_token: str, db_session: Session):
    headers = {"Authorization": f"Bearer {authenticated_user_token}"}
    # Create a supplier to ensure list is not empty
    db_session.add(models.Supplier(name="Supplier Gamma", contactInfo="gamma@supplier.com"))
    db_session.commit()

    response = await client.get("/api/suppliers/all", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(s["name"] == "Supplier Gamma" for s in data)

async def test_read_specific_supplier(client: AsyncClient, authenticated_user_token: str, db_session: Session):
    headers = {"Authorization": f"Bearer {authenticated_user_token}"}
    supplier = models.Supplier(name="Supplier Delta", contactInfo="delta@supplier.com")
    db_session.add(supplier)
    db_session.commit()
    db_session.refresh(supplier)

    response = await client.get(f"/api/suppliers/{supplier.id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == supplier.name
    assert data["id"] == supplier.id

async def test_read_specific_supplier_not_found(client: AsyncClient, authenticated_user_token: str):
    headers = {"Authorization": f"Bearer {authenticated_user_token}"}
    response = await client.get("/api/suppliers/7777", headers=headers) # Non-existent
    assert response.status_code == 404

async def test_update_supplier_success(client: AsyncClient, authenticated_user_token: str, db_session: Session):
    headers = {"Authorization": f"Bearer {authenticated_user_token}"}
    supplier = models.Supplier(name="Supplier Epsilon", contactInfo="epsilon@supplier.com")
    db_session.add(supplier)
    db_session.commit()
    db_session.refresh(supplier)

    update_data = {"name": "Supplier Epsilon Updated", "contactInfo": "updated@supplier.com", "address": "Updated Address"}
    response = await client.put(f"/api/suppliers/update/{supplier.id}", json=update_data, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["contactInfo"] == update_data["contactInfo"]

    db_session.expire(supplier) # Expire to get fresh data from DB
    updated_supplier_in_db = db_session.query(models.Supplier).filter(models.Supplier.id == supplier.id).first()
    assert updated_supplier_in_db.address == update_data["address"]


async def test_delete_supplier_success(client: AsyncClient, authenticated_user_token: str, db_session: Session):
    headers = {"Authorization": f"Bearer {authenticated_user_token}"}
    supplier = models.Supplier(name="Supplier Zeta", contactInfo="zeta@supplier.com")
    db_session.add(supplier)
    db_session.commit()
    db_session.refresh(supplier)

    response = await client.delete(f"/api/suppliers/delete/{supplier.id}", headers=headers)
    assert response.status_code == 200
    assert db_session.query(models.Supplier).filter(models.Supplier.id == supplier.id).first() is None

async def test_delete_supplier_with_transactions_forbidden(client: AsyncClient, authenticated_user_token: str, db_session: Session):
    headers = {"Authorization": f"Bearer {authenticated_user_token}"}
    # Create supplier
    supplier_with_trans = models.Supplier(name="Supplier Eta", contactInfo="eta@supplier.com")
    db_session.add(supplier_with_trans)
    db_session.commit()
    db_session.refresh(supplier_with_trans)

    # Create a user for the transaction
    user = db_session.query(models.User).filter(models.User.email == "testuser_functional@example.com").first()
    if not user: # Should be created by authenticated_user_token fixture, but as a fallback
        from backend.security import get_password_hash
        user = models.User(email="testuser_functional@example.com", password=get_password_hash("test"), name="Tx User", role=models.UserRole.USER)
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)


    # Create a transaction associated with this supplier
    transaction = models.Transaction(
        totalProducts=1,
        totalPrice=100,
        transactionType=schemas.TransactionType.PURCHASE,
        user_id=user.id,
        supplier_id=supplier_with_trans.id
    )
    db_session.add(transaction)
    db_session.commit()

    response = await client.delete(f"/api/suppliers/delete/{supplier_with_trans.id}", headers=headers)
    assert response.status_code == 400
    assert "Cannot delete supplier with associated transactions" in response.json()["detail"]
