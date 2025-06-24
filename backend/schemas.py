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
    stock: int = Field(default=0, description="庫存數量")  # 添加庫存欄位
    is_deleted: bool = Field(default=False, description="是否已刪除")
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[int] = None
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
    stock: Optional[int] = Field(None, ge=0, description="庫存數量，必須大於等於0")  # 添加庫存更新


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

# 入庫單相關的枚舉類型
class GoodsReceiptStatus(str, enum.Enum):
    DRAFT = "DRAFT"           # 草稿
    PENDING = "PENDING"       # 待處理
    COMPLETED = "COMPLETED"   # 已完成
    CANCELLED = "CANCELLED"   # 已取消

class WarehouseType(str, enum.Enum):
    MAIN = "MAIN"             # 主倉
    RAW_MATERIAL = "RAW_MATERIAL"  # 原料倉
    FINISHED_GOODS = "FINISHED_GOODS"  # 成品倉
    QUARANTINE = "QUARANTINE" # 檢疫倉
    DAMAGED = "DAMAGED"       # 損壞品倉

# 銷售單相關的枚舉類型
class SalesOrderStatus(str, enum.Enum):
    DRAFT = "DRAFT"           # 草稿
    CONFIRMED = "CONFIRMED"   # 已確認
    SHIPPED = "SHIPPED"       # 已出貨
    DELIVERED = "DELIVERED"   # 已送達
    CANCELLED = "CANCELLED"   # 已取消

class PaymentTerm(str, enum.Enum):
    CASH = "CASH"             # 現金
    MONTHLY = "MONTHLY"       # 月結
    TRANSFER = "TRANSFER"     # 轉帳
    CREDIT_CARD = "CREDIT_CARD"  # 信用卡
    CHECK = "CHECK"           # 支票


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


# 入庫明細項目 schemas
class GoodsReceiptItemBase(BaseModel):
    purchase_order_item_id: int = Field(..., description="採購明細ID")
    product_id: int = Field(..., description="產品ID")
    ordered_quantity: int = Field(..., gt=0, description="採購數量")
    received_quantity: int = Field(..., ge=0, description="實到數量，必須大於等於0")
    storage_location: Optional[str] = None
    notes: Optional[str] = None

class GoodsReceiptItemCreate(GoodsReceiptItemBase):
    pass

class GoodsReceiptItemUpdate(BaseModel):
    purchase_order_item_id: Optional[int] = None  # 需要用來識別明細項目
    product_id: Optional[int] = None              # 需要用來識別產品
    received_quantity: Optional[int] = Field(None, ge=0)
    storage_location: Optional[str] = None
    notes: Optional[str] = None

class GoodsReceiptItem(GoodsReceiptItemBase):
    id: int
    product: Optional[Product] = None  # 包含產品詳細資訊
    purchase_order_item: Optional[PurchaseOrderItem] = None  # 包含採購明細資訊
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# 入庫單主檔 schemas
class GoodsReceiptBase(BaseModel):
    receipt_date: date = Field(..., description="入庫日期")
    purchase_order_id: int = Field(..., description="採購單ID")
    warehouse_type: WarehouseType = WarehouseType.MAIN
    warehouse_location: Optional[str] = None
    notes: Optional[str] = None

class GoodsReceiptCreate(GoodsReceiptBase):
    items: List[GoodsReceiptItemCreate] = Field(..., min_items=1, description="入庫明細，至少要有一項")

class GoodsReceiptUpdate(BaseModel):
    receipt_date: Optional[date] = None
    warehouse_type: Optional[WarehouseType] = None
    warehouse_location: Optional[str] = None
    status: Optional[GoodsReceiptStatus] = None
    notes: Optional[str] = None
    items: Optional[List[GoodsReceiptItemUpdate]] = None  # 新增入庫明細更新

class GoodsReceipt(GoodsReceiptBase):
    id: int
    gr_number: str  # 入庫單號
    warehouse_staff_id: int
    status: GoodsReceiptStatus
    created_at: datetime
    updated_at: Optional[datetime] = None

    # 關聯資料
    warehouse_staff: Optional[User] = None
    purchase_order: Optional[PurchaseOrder] = None
    items: List[GoodsReceiptItem] = []

    class Config:
        from_attributes = True


# 銷售明細項目 schemas
class SalesOrderItemBase(BaseModel):
    product_id: int = Field(..., description="產品ID")
    quantity: int = Field(..., gt=0, description="數量，必須大於0")
    unit_price: float = Field(..., ge=0, description="單價，必須大於等於0")
    notes: Optional[str] = None

class SalesOrderItemCreate(SalesOrderItemBase):
    pass

class SalesOrderItemUpdate(BaseModel):
    product_id: Optional[int] = None
    quantity: Optional[int] = Field(None, gt=0)
    unit_price: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = None

class SalesOrderItem(SalesOrderItemBase):
    id: int
    line_total: float  # 小計 (數量 × 單價)
    product: Optional[Product] = None  # 包含產品詳細資訊
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# 銷售單主檔 schemas
class SalesOrderBase(BaseModel):
    sales_date: date = Field(..., description="銷售日期")
    customer_id: int = Field(..., description="客戶ID")
    payment_term: PaymentTerm = PaymentTerm.CASH
    notes: Optional[str] = None
    tax_type: TaxType = TaxType.INCLUSIVE
    tax_rate: float = Field(0.05, ge=0, le=1, description="稅率，0-1之間")
    discount_rate: float = Field(0.0, ge=0, le=1, description="折扣率，0-1之間")

class SalesOrderCreate(SalesOrderBase):
    items: List[SalesOrderItemCreate] = Field(..., min_items=1, description="銷售明細，至少要有一項")

class SalesOrderUpdate(BaseModel):
    sales_date: Optional[date] = None
    customer_id: Optional[int] = None
    payment_term: Optional[PaymentTerm] = None
    status: Optional[SalesOrderStatus] = None
    notes: Optional[str] = None
    tax_type: Optional[TaxType] = None
    tax_rate: Optional[float] = Field(None, ge=0, le=1)
    discount_rate: Optional[float] = Field(None, ge=0, le=1)
    items: Optional[List[SalesOrderItemUpdate]] = None  # 銷售明細更新

class SalesOrder(SalesOrderBase):
    id: int
    so_number: str  # 銷售單號
    salesperson_id: int
    status: SalesOrderStatus
    subtotal: float  # 小計
    tax_amount: float  # 稅額
    discount_amount: float  # 折扣金額
    total_amount: float  # 實收總額
    created_at: datetime
    updated_at: Optional[datetime] = None

    # 關聯資料
    salesperson: Optional[User] = None
    customer: Optional[Customer] = None
    items: List[SalesOrderItem] = []

    class Config:
        from_attributes = True
