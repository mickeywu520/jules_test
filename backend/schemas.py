from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Union
from datetime import datetime, date
import enum

# Import Enum types from models.py to be used in Pydantic schemas
# This avoids redefining them and ensures consistency.
# We might need to adjust models.py if enums are defined in a way that's hard to import directly
# For now, let's assume we can import them or we'll redefine for Pydantic if necessary.
# For simplicity in this step, I'll redefine them here. If issues arise, we can refactor.

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    USER = "USER"

class TransactionType(str, enum.Enum):
    PURCHASE = "PURCHASE"
    SELL = "SELL"

class TransactionStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING" # Added PROCESSING status
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

# CustomerType 和 PaymentCategory 改為字串類型，支援動態值
# PaymentMethod 改為支援動態字串，如 "月結30天", "下收" 等

# Base and Read schemas for Category
class CategoryBase(BaseModel):
    name: str

class CategoryCreate(CategoryBase):
    pass

class Category(CategoryBase): # For Read operations
    id: int

    class Config:
        from_attributes = True

# Base and Read schemas for Product - 根據客戶 Excel 欄位重新設計
class ProductBase(BaseModel):
    productCode: str = Field(..., description="貨品編號，必須唯一")
    productName: str = Field(..., description="貨品名稱")
    unit: str = Field(..., description="單位（箱、盒等）")
    warehouse: Optional[str] = None  # 倉別
    unitWeight: Optional[float] = None  # 單位重量(KG)
    barcode: Optional[str] = None  # 條碼編號
    category_id: int = Field(..., description="類別ID")

class ProductCreate(ProductBase):
    pass

# For Read operations
class Product(ProductBase):
    id: int
    createdAt: datetime
    updatedAt: Optional[datetime] = None
    category: Optional[Category] = None  # 包含類別詳細資訊

    class Config:
        from_attributes = True

# Schemas for updating a product (all fields optional)
class ProductUpdate(BaseModel):
    productCode: Optional[str] = None
    productName: Optional[str] = None
    unit: Optional[str] = None
    warehouse: Optional[str] = None
    unitWeight: Optional[float] = None
    barcode: Optional[str] = None
    category_id: Optional[int] = None


# Base and Read schemas for Supplier
class SupplierBase(BaseModel):
    name: str
    contactInfo: Optional[str] = None
    address: Optional[str] = None

class SupplierCreate(SupplierBase):
    pass

class Supplier(SupplierBase): # For Read operations
    id: int

    class Config:
        from_attributes = True

# Base and Read schemas for Customer
class CustomerBase(BaseModel):
    customerType: str
    salesPersonId: Optional[str] = None
    salesPersonName: Optional[str] = None
    customerCode: str = Field(..., description="客戶編號，必須唯一")
    customerName: str = Field(..., description="客戶名稱")
    contactPerson: Optional[str] = None
    invoiceTitle: Optional[str] = None
    taxId: Optional[str] = None
    phoneNumber: Optional[str] = None
    faxNumber: Optional[str] = None
    deliveryAddress: Optional[str] = None
    businessHours: Optional[str] = None
    paymentMethod: Optional[str] = None
    paymentCategory: Optional[str] = None
    creditLimit: Optional[float] = 0.0

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(BaseModel):
    customerType: Optional[str] = None
    salesPersonId: Optional[str] = None
    salesPersonName: Optional[str] = None
    customerCode: Optional[str] = None
    customerName: Optional[str] = None
    contactPerson: Optional[str] = None
    invoiceTitle: Optional[str] = None
    taxId: Optional[str] = None
    phoneNumber: Optional[str] = None
    faxNumber: Optional[str] = None
    deliveryAddress: Optional[str] = None
    businessHours: Optional[str] = None
    paymentMethod: Optional[str] = None
    paymentCategory: Optional[str] = None
    creditLimit: Optional[float] = None

class Customer(CustomerBase): # For Read operations
    id: int
    createdDate: datetime
    updatedAt: Optional[datetime] = None

    class Config:
        from_attributes = True

# Base and Read schemas for User
class UserBase(BaseModel):
    name: Optional[str] = None
    email: EmailStr
    phoneNumber: Optional[str] = None
    role: Optional[UserRole] = UserRole.USER

class UserCreate(UserBase):
    password: str = Field(..., min_length=4) # Example: make password required on create

class UserUpdate(BaseModel): # For updating user profile
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phoneNumber: Optional[str] = None
    # Role and password updates might be handled by separate, more secure endpoints or admin functions

class User(UserBase): # For Read operations (e.g., /users/current)
    id: int
    createdAt: datetime
    # Do not include password in responses

    class Config:
        from_attributes = True


# Schemas for TransactionProductAssociation (if needed directly in API, often handled via Transaction)
class TransactionProductAssociationBase(BaseModel):
    product_id: int
    quantity: Optional[int] = 1

class TransactionProductAssociationCreate(TransactionProductAssociationBase):
    pass

class TransactionProductAssociation(TransactionProductAssociationBase): # For Read
    # Potentially include product details if needed when reading this association directly
    # product: Product # This could cause circular dependencies if not handled carefully.
    # For now, keeping it simple as the frontend likely gets product details via the Transaction schema.
    pass
    class Config:
        from_attributes = True


# Base and Read schemas for Transaction
class TransactionBase(BaseModel):
    totalProducts: int
    totalPrice: float
    transactionType: TransactionType
    transactionStatus: Optional[TransactionStatus] = TransactionStatus.PENDING
    description: Optional[str] = None
    note: Optional[str] = None
    user_id: Optional[int] = None # Assuming user_id is set based on authenticated user
    supplier_id: Optional[int] = None
    # For creating transactions, the frontend might send a list of products involved
    # This needs to align with how api.service.ts sends data for purchase/sell
    # For example: products_involved: List[TransactionProductAssociationCreate]

class TransactionCreate(TransactionBase):
    # The frontend's purchaseProduct/sellProduct takes a 'body'. We need to match that structure.
    # If 'body' contains a list of product IDs and quantities:
    products_involved: List[TransactionProductAssociationCreate]


class Transaction(TransactionBase): # For Read operations
    id: int
    createdAt: datetime
    updatedAt: Optional[datetime] = None
    user: Optional[User] = None # Nested user details
    supplier: Optional[Supplier] = None # Nested supplier details
    products: List[TransactionProductAssociation] # List of products involved in the transaction

    class Config:
        from_attributes = True

# Schema for updating transaction status (as per frontend api.service.ts)
class TransactionStatusUpdate(BaseModel):
    status: TransactionStatus # Frontend sends JSON.stringify(status) - need to ensure this matches

# Schemas for Authentication
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str


# 採購單相關的枚舉類型
class PurchaseOrderStatus(str, enum.Enum):
    DRAFT = "DRAFT"           # 草稿
    PENDING = "PENDING"       # 待處理
    CONFIRMED = "CONFIRMED"   # 已確認
    RECEIVED = "RECEIVED"     # 已收貨
    CANCELLED = "CANCELLED"   # 已取消

class PaymentStatus(str, enum.Enum):
    UNPAID = "UNPAID"         # 未付款
    PARTIAL = "PARTIAL"       # 部分付款
    PAID = "PAID"             # 已付款

class TaxType(str, enum.Enum):
    INCLUSIVE = "INCLUSIVE"   # 含稅
    EXCLUSIVE = "EXCLUSIVE"   # 未稅
    ADDITIONAL = "ADDITIONAL" # 外加稅


# 採購明細項目 schemas
class PurchaseOrderItemBase(BaseModel):
    product_id: int = Field(..., description="產品ID")
    quantity: int = Field(..., gt=0, description="數量，必須大於0")
    unit_price: float = Field(..., ge=0, description="單價，必須大於等於0")
    notes: Optional[str] = None

class PurchaseOrderItemCreate(PurchaseOrderItemBase):
    pass

class PurchaseOrderItemUpdate(BaseModel):
    product_id: Optional[int] = None
    quantity: Optional[int] = Field(None, gt=0)
    unit_price: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = None

class PurchaseOrderItem(PurchaseOrderItemBase):
    id: int
    line_total: float  # 小計 (數量 × 單價)
    product: Optional[Product] = None  # 包含產品詳細資訊
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# 採購單主檔 schemas
class PurchaseOrderBase(BaseModel):
    purchase_date: date = Field(..., description="採購日期")
    expected_delivery_date: Optional[date] = None
    supplier_id: int = Field(..., description="供應商ID")
    notes: Optional[str] = None
    tax_type: TaxType = TaxType.INCLUSIVE
    tax_rate: float = Field(0.05, ge=0, le=1, description="稅率，0-1之間")
    payment_method: Optional[str] = None

class PurchaseOrderCreate(PurchaseOrderBase):
    items: List[PurchaseOrderItemCreate] = Field(..., min_items=1, description="採購明細，至少要有一項")

class PurchaseOrderUpdate(BaseModel):
    purchase_date: Optional[date] = None
    expected_delivery_date: Optional[date] = None
    supplier_id: Optional[int] = None
    status: Optional[PurchaseOrderStatus] = None
    notes: Optional[str] = None
    tax_type: Optional[TaxType] = None
    tax_rate: Optional[float] = Field(None, ge=0, le=1)
    payment_method: Optional[str] = None
    payment_status: Optional[PaymentStatus] = None

class PurchaseOrder(PurchaseOrderBase):
    id: int
    po_number: str  # 採購單號
    purchaser_id: int
    status: PurchaseOrderStatus
    subtotal: float  # 小計
    tax_amount: float  # 稅額
    total_amount: float  # 含稅總額
    payment_status: PaymentStatus
    created_at: datetime
    updated_at: Optional[datetime] = None

    # 關聯資料
    purchaser: Optional[User] = None
    supplier: Optional[Supplier] = None
    items: List[PurchaseOrderItem] = []

    class Config:
        from_attributes = True
