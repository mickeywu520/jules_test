import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session
import os
from io import BytesIO

from backend import models, schemas

import pytest_asyncio # Import for the fixture decorator

pytestmark = pytest.mark.asyncio

# Helper to get a category ID for product tests
@pytest_asyncio.fixture(scope="function") # Changed to @pytest_asyncio.fixture
async def test_category_id(db_session: Session, client: AsyncClient, authenticated_user_token: str) -> int:
    headers = {"Authorization": f"Bearer {authenticated_user_token}"}
    category_data = {"name": f"Test Category For Products {os.urandom(4).hex()}"} # Unique name
    response = await client.post("/api/categories/add", json=category_data, headers=headers)
    assert response.status_code == 201
    return response.json()["id"]

# --- Product Tests ---

async def test_add_product_success_with_image(client: AsyncClient, authenticated_user_token: str, test_category_id: int, db_session: Session):
    headers = {"Authorization": f"Bearer {authenticated_user_token}"}
    product_data = {
        "name": "Test Product Alpha",
        "price": "19.99", # Form data sends strings
        "category_id": str(test_category_id),
        "stockQuantity": "50",
        "description": "A great product"
    }
    # Simulate file upload
    files = {"image": ("test_image.png", BytesIO(b"fakeimagedata"), "image/png")}

    response = await client.post("/api/products/add", data=product_data, files=files, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == product_data["name"]
    assert data["price"] == float(product_data["price"])
    assert data["imageUrl"] is not None
    assert data["imageUrl"].startswith("/static/product_images/")

    # Check if image file exists (simple check, actual file content not verified here)
    image_filename = data["imageUrl"].split("/")[-1]
    image_path = os.path.join("backend/static/product_images", image_filename)
    assert os.path.exists(image_path)

    # Clean up created image
    if os.path.exists(image_path):
        os.remove(image_path)

async def test_add_product_success_without_image(client: AsyncClient, authenticated_user_token: str, test_category_id: int, db_session: Session):
    headers = {"Authorization": f"Bearer {authenticated_user_token}"}
    product_data = {
        "name": "Test Product Beta",
        "price": "29.99",
        "category_id": str(test_category_id),
    }
    # No files dictionary for no image
    response = await client.post("/api/products/add", data=product_data, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == product_data["name"]
    assert data["imageUrl"] is None

async def test_add_product_invalid_category(client: AsyncClient, authenticated_user_token: str):
    headers = {"Authorization": f"Bearer {authenticated_user_token}"}
    product_data = {"name": "Product Bad Category", "price": "10", "category_id": "99999"} # Non-existent category
    response = await client.post("/api/products/add", data=product_data, headers=headers)
    assert response.status_code == 404 # Category not found

async def test_read_all_products(client: AsyncClient, authenticated_user_token: str, test_category_id: int, db_session: Session):
    headers = {"Authorization": f"Bearer {authenticated_user_token}"}
    # Add a product to ensure the list is not empty
    db_session.add(models.Product(name="Product Gamma", price=1.0, category_id=test_category_id))
    db_session.commit()

    response = await client.get("/api/products/all", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(p["name"] == "Product Gamma" for p in data)

async def test_read_specific_product(client: AsyncClient, authenticated_user_token: str, test_category_id: int, db_session: Session):
    headers = {"Authorization": f"Bearer {authenticated_user_token}"}
    product = models.Product(name="Product Delta", price=1.0, category_id=test_category_id)
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)

    response = await client.get(f"/api/products/{product.id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == product.name
    assert data["id"] == product.id
    assert data["category"]["id"] == test_category_id # Check nested category

async def test_update_product_success_with_new_image(client: AsyncClient, authenticated_user_token: str, test_category_id: int, db_session: Session):
    headers = {"Authorization": f"Bearer {authenticated_user_token}"}
    # Create initial product with an image
    initial_image_name = "initial_image.png"
    initial_image_path_part = f"/static/product_images/{initial_image_name}" # Simplified

    # Create a dummy initial image file for the product to have an imageUrl
    os.makedirs("backend/static/product_images", exist_ok=True)
    dummy_initial_image_abs_path = f"backend/static/product_images/{initial_image_name}"
    with open(dummy_initial_image_abs_path, "wb") as f:
        f.write(b"oldimage")

    product = models.Product(name="Product Epsilon", price=12.34, category_id=test_category_id, imageUrl=initial_image_path_part)
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)

    update_form_data = {
        "id": str(product.id),
        "name": "Product Epsilon Updated",
        "price": "99.99"
    }
    files = {"image": ("new_image.png", BytesIO(b"newimagedata"), "image/png")}

    response = await client.put("/api/products/update", data=update_form_data, files=files, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_form_data["name"]
    assert data["imageUrl"] is not None
    assert data["imageUrl"] != initial_image_path_part # New image URL

    # Check new image exists, old one ideally deleted (though delete_product_image has specific path logic)
    new_image_filename = data["imageUrl"].split("/")[-1]
    new_image_path = os.path.join("backend/static/product_images", new_image_filename)
    assert os.path.exists(new_image_path)
    # assert not os.path.exists(dummy_initial_image_abs_path) # This depends on how delete_product_image constructs paths

    # Clean up
    if os.path.exists(new_image_path): os.remove(new_image_path)
    if os.path.exists(dummy_initial_image_abs_path): os.remove(dummy_initial_image_abs_path) # Ensure cleanup

async def test_delete_product_success(client: AsyncClient, authenticated_user_token: str, test_category_id: int, db_session: Session):
    headers = {"Authorization": f"Bearer {authenticated_user_token}"}
    # Create product with an image
    image_name = "delete_me.png"
    image_url = f"/static/product_images/{image_name}"
    os.makedirs("backend/static/product_images", exist_ok=True)
    image_abs_path = f"backend/static/product_images/{image_name}"
    with open(image_abs_path, "wb") as f: f.write(b"deletethis")

    product = models.Product(name="Product ToDelete", price=5.0, category_id=test_category_id, imageUrl=image_url)
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)

    assert os.path.exists(image_abs_path) # Pre-check

    response = await client.delete(f"/api/products/delete/{product.id}", headers=headers)
    assert response.status_code == 200
    assert db_session.query(models.Product).filter(models.Product.id == product.id).first() is None
    assert not os.path.exists(image_abs_path) # Check image was deleted

async def test_delete_product_with_transactions_forbidden(client: AsyncClient, authenticated_user_token: str, test_category_id: int, db_session: Session):
    headers = {"Authorization": f"Bearer {authenticated_user_token}"}
    product_in_trans = models.Product(name="Product In Transaction", price=1.0, category_id=test_category_id)
    db_session.add(product_in_trans)
    db_session.commit()
    db_session.refresh(product_in_trans)

    # Create a user for the transaction
    user = db_session.query(models.User).filter(models.User.email == "testuser_functional@example.com").first()
    # Create a transaction
    transaction = models.Transaction(totalProducts=1, totalPrice=1, transactionType=schemas.TransactionType.SELL, user_id=user.id)
    db_session.add(transaction)
    db_session.commit()
    db_session.refresh(transaction)
    # Create association
    assoc = models.TransactionProductAssociation(transaction_id=transaction.id, product_id=product_in_trans.id, quantity=1)
    db_session.add(assoc)
    db_session.commit()

    response = await client.delete(f"/api/products/delete/{product_in_trans.id}", headers=headers)
    assert response.status_code == 400
    assert "Cannot delete product with ID" in response.json()["detail"]
    assert "it is part of existing transactions" in response.json()["detail"]
