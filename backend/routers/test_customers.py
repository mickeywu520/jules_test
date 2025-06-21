import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.orm import Session

from backend.main import app
from backend import models, schemas

# Mark all tests in this module as async
pytestmark = pytest.mark.asyncio

class TestCustomers:
    
    async def test_create_customer(self, client: AsyncClient, db_session: Session):
        """Test creating a new customer"""
        customer_data = {
            "customerType": "COMPANY",
            "salesPersonId": "SP001",
            "salesPersonName": "張三",
            "customerCode": "CUST001",
            "customerName": "測試公司有限公司",
            "contactPerson": "李四",
            "invoiceTitle": "測試公司有限公司",
            "taxId": "12345678",
            "phoneNumber": "02-12345678",
            "faxNumber": "02-87654321",
            "deliveryAddress": "台北市信義區信義路五段7號",
            "businessHours": "週一至週五 9:00-18:00",
            "paymentMethod": "MONTHLY_PAYMENT",
            "paymentCategory": "MONTHLY_SETTLEMENT",
            "creditLimit": 100000.0
        }
        
        response = await client.post("/api/customers/add", json=customer_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["customerCode"] == "CUST001"
        assert data["customerName"] == "測試公司有限公司"
        assert data["customerType"] == "COMPANY"
        assert data["creditLimit"] == 100000.0

    async def test_create_duplicate_customer_code(self, client: AsyncClient, db_session: Session):
        """Test creating a customer with duplicate customer code should fail"""
        customer_data = {
            "customerType": "COMPANY",
            "customerCode": "CUST001",
            "customerName": "測試公司1"
        }
        
        # Create first customer
        await client.post("/api/customers/add", json=customer_data)
        
        # Try to create second customer with same code
        customer_data["customerName"] = "測試公司2"
        response = await client.post("/api/customers/add", json=customer_data)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    async def test_get_all_customers(self, client: AsyncClient, db_session: Session):
        """Test getting all customers"""
        # Create a test customer first
        customer_data = {
            "customerType": "INDIVIDUAL",
            "customerCode": "CUST002",
            "customerName": "個人客戶"
        }
        await client.post("/api/customers/add", json=customer_data)
        
        response = await client.get("/api/customers/all")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    async def test_get_customer_by_id(self, client: AsyncClient, db_session: Session):
        """Test getting a customer by ID"""
        # Create a test customer first
        customer_data = {
            "customerType": "COMPANY",
            "customerCode": "CUST003",
            "customerName": "測試公司3"
        }
        create_response = await client.post("/api/customers/add", json=customer_data)
        customer_id = create_response.json()["id"]
        
        response = await client.get(f"/api/customers/{customer_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == customer_id
        assert data["customerCode"] == "CUST003"

    async def test_get_customer_by_code(self, client: AsyncClient, db_session: Session):
        """Test getting a customer by customer code"""
        # Create a test customer first
        customer_data = {
            "customerType": "COMPANY",
            "customerCode": "CUST004",
            "customerName": "測試公司4"
        }
        await client.post("/api/customers/add", json=customer_data)
        
        response = await client.get("/api/customers/code/CUST004")
        assert response.status_code == 200
        
        data = response.json()
        assert data["customerCode"] == "CUST004"

    async def test_update_customer(self, client: AsyncClient, db_session: Session):
        """Test updating a customer"""
        # Create a test customer first
        customer_data = {
            "customerType": "COMPANY",
            "customerCode": "CUST005",
            "customerName": "測試公司5"
        }
        create_response = await client.post("/api/customers/add", json=customer_data)
        customer_id = create_response.json()["id"]
        
        # Update the customer
        update_data = {
            "customerName": "更新後的公司名稱",
            "phoneNumber": "02-99999999"
        }
        response = await client.put(f"/api/customers/update/{customer_id}", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["customerName"] == "更新後的公司名稱"
        assert data["phoneNumber"] == "02-99999999"

    async def test_search_customers(self, client: AsyncClient, db_session: Session):
        """Test searching customers by name"""
        # Create test customers
        customers = [
            {"customerType": "COMPANY", "customerCode": "SEARCH001", "customerName": "搜尋測試公司1"},
            {"customerType": "COMPANY", "customerCode": "SEARCH002", "customerName": "搜尋測試公司2"},
            {"customerType": "INDIVIDUAL", "customerCode": "SEARCH003", "customerName": "其他公司"}
        ]
        
        for customer in customers:
            await client.post("/api/customers/add", json=customer)
        
        response = await client.get("/api/customers/search/搜尋測試")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 2
        assert all("搜尋測試" in customer["customerName"] for customer in data)

    async def test_delete_customer(self, client: AsyncClient, db_session: Session):
        """Test deleting a customer"""
        # Create a test customer first
        customer_data = {
            "customerType": "COMPANY",
            "customerCode": "DELETE001",
            "customerName": "待刪除公司"
        }
        create_response = await client.post("/api/customers/add", json=customer_data)
        customer_id = create_response.json()["id"]
        
        # Delete the customer
        response = await client.delete(f"/api/customers/delete/{customer_id}")
        assert response.status_code == 200
        
        # Verify customer is deleted
        get_response = await client.get(f"/api/customers/{customer_id}")
        assert get_response.status_code == 404
