from sqlalchemy import Column, Integer, String, Float, DateTime, Date, ForeignKey, Enum as SQLAlchemyEnum, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func # For default DateTime values
import enum

from .database import Base # Import Base from database.py

# Define Enum types if needed by the schema (e.g., for TransactionType, TransactionStatus, UserRole)
class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    USER = "USER" # Assuming a general user role

class TransactionType(str, enum.Enum):
    PURCHASE = "PURCHASE"
    SELL = "SELL"

class TransactionStatus(str, enum.Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    # Add other statuses as per your frontend's expectations for 'updateTransactionStatus'

# 採購單狀態
class PurchaseOrderStatus(str, enum.Enum):
    DRAFT = "DRAFT"           # 草稿
    PENDING = "PENDING"       # 待處理
    CONFIRMED = "CONFIRMED"   # 已確認
    RECEIVED = "RECEIVED"     # 已收貨
    CANCELLED = "CANCELLED"   # 已取消

# 付款狀態
class PaymentStatus(str, enum.Enum):
    UNPAID = "UNPAID"         # 未付款
    PARTIAL = "PARTIAL"       # 部分付款
    PAID = "PAID"             # 已付款

# 稅務類型
class TaxType(str, enum.Enum):
    INCLUSIVE = "INCLUSIVE"   # 含稅
    EXCLUSIVE = "EXCLUSIVE"   # 未稅
    ADDITIONAL = "ADDITIONAL" # 外加稅

# 入庫單狀態
class GoodsReceiptStatus(str, enum.Enum):
    DRAFT = "DRAFT"           # 草稿
    PENDING = "PENDING"       # 待處理
    COMPLETED = "COMPLETED"   # 已完成
    CANCELLED = "CANCELLED"   # 已取消

# 倉庫類型
class WarehouseType(str, enum.Enum):
    MAIN = "MAIN"             # 主倉
    RAW_MATERIAL = "RAW_MATERIAL"  # 原料倉
    FINISHED_GOODS = "FINISHED_GOODS"  # 成品倉
    QUARANTINE = "QUARANTINE" # 檢疫倉
    DAMAGED = "DAMAGED"       # 損壞品倉

# 銷售單狀態
class SalesOrderStatus(str, enum.Enum):
    DRAFT = "DRAFT"           # 草稿
    CONFIRMED = "CONFIRMED"   # 已確認
    SHIPPED = "SHIPPED"       # 已出貨
    DELIVERED = "DELIVERED"   # 已送達
    CANCELLED = "CANCELLED"   # 已取消

# 付款條件
class PaymentTerm(str, enum.Enum):
    CASH = "CASH"             # 現金
    MONTHLY = "MONTHLY"       # 月結
    TRANSFER = "TRANSFER"     # 轉帳
    CREDIT_CARD = "CREDIT_CARD"  # 信用卡
    CHECK = "CHECK"           # 支票

# CustomerType, PaymentMethod, PaymentCategory 改為字串類型，支援動態值
# 例如：customerType = "區域連鎖", paymentMethod = "月結30天", paymentCategory = "支票"

# User Model
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False) # Hashed password
    phoneNumber = Column(String, nullable=True)
    role = Column(SQLAlchemyEnum(UserRole), default=UserRole.USER)
    createdAt = Column(DateTime(timezone=True), server_default=func.now())

    transactions = relationship("Transaction", back_populates="user")

# Category Model - 恢復與 Product 的關聯
class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)

    # 恢復與 Product 的關聯
    products = relationship("Product", back_populates="category")

# Supplier Model
class Supplier(Base):
    __tablename__ = "suppliers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    contactInfo = Column(String, nullable=True)
    address = Column(Text, nullable=True)

    transactions = relationship("Transaction", back_populates="supplier")

# Customer Model
class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, index=True)
    customerType = Column(String, nullable=False)  # 客戶類型 (字串類型，支援動態值)
    createdDate = Column(DateTime(timezone=True), server_default=func.now())  # 建檔日期
    salesPersonId = Column(String, nullable=True)  # 業務員編號
    salesPersonName = Column(String, nullable=True)  # 業務員名稱
    customerCode = Column(String, unique=True, index=True, nullable=False)  # 客戶編號
    customerName = Column(String, index=True, nullable=False)  # 客戶名稱
    contactPerson = Column(String, nullable=True)  # 客戶聯絡人
    invoiceTitle = Column(String, nullable=True)  # 發票抬頭
    taxId = Column(String, nullable=True)  # 統一編號
    phoneNumber = Column(String, nullable=True)  # 電話號碼
    faxNumber = Column(String, nullable=True)  # 傳真號碼
    deliveryAddress = Column(Text, nullable=True)  # 送貨地址
    businessHours = Column(Text, nullable=True)  # 營業時間/公休日
    paymentMethod = Column(String, nullable=True)  # 收款方式 (支援動態月結天數，如 "月結30天")
    paymentCategory = Column(String, nullable=True)  # 收款類別 (字串類型，支援動態值)
    creditLimit = Column(Float, nullable=True, default=0.0)  # 銷貨額度
    updatedAt = Column(DateTime(timezone=True), onupdate=func.now())

    # 可以添加與交易的關聯（如果需要的話）
    # transactions = relationship("Transaction", back_populates="customer")

# Product Model - 根據客戶 Excel 欄位重新設計
class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    productCode = Column(String, unique=True, index=True, nullable=False)  # 貨品編號
    productName = Column(String, index=True, nullable=False)  # 貨品名稱
    unit = Column(String, nullable=False)  # 單位（箱、盒等）
    warehouse = Column(String, nullable=True)  # 倉別
    unitWeight = Column(Float, nullable=True)  # 單位重量(KG)
    barcode = Column(String, nullable=True)  # 條碼編號
    stock = Column(Integer, default=0, nullable=False)  # 庫存數量，預設為0

    # 軟刪除相關欄位
    is_deleted = Column(Boolean, default=False, nullable=False)  # 軟刪除標記
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # 刪除時間
    deleted_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # 刪除者

    createdAt = Column(DateTime(timezone=True), server_default=func.now())
    updatedAt = Column(DateTime(timezone=True), onupdate=func.now())

    # 與 Category 的關聯
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    category = relationship("Category", back_populates="products")

    # 軟刪除關聯
    deleted_by_user = relationship("User", foreign_keys=[deleted_by])

    # 保留與交易的關聯
    transactions = relationship("TransactionProductAssociation", back_populates="product")


# Transaction Model
class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    totalProducts = Column(Integer, nullable=False) # Or could be calculated
    totalPrice = Column(Float, nullable=False)
    transactionType = Column(SQLAlchemyEnum(TransactionType), nullable=False, name="transaction_type_enum")
    transactionStatus = Column(SQLAlchemyEnum(TransactionStatus), default=TransactionStatus.PENDING, name="transaction_status_enum")
    description = Column(Text, nullable=True)
    note = Column(Text, nullable=True)
    updatedAt = Column(DateTime(timezone=True), onupdate=func.now())
    createdAt = Column(DateTime(timezone=True), server_default=func.now())

    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="transactions")

    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True) # A transaction might not always have a supplier (e.g., a direct sell)
    supplier = relationship("Supplier", back_populates="transactions")

    # For Many-to-Many relationship between Transaction and Product
    products = relationship("TransactionProductAssociation", back_populates="transaction")

# Association table for Many-to-Many relationship between Transaction and Product
# Based on your schema, a transaction seems to be linked to *a* product, but the `totalProducts`
# field suggests a transaction could involve quantities of multiple products.
# The schema `Transaction -> Product -> PRODUCT` is a bit ambiguous for a list.
# If a transaction can have many products and a product can be in many transactions:
class TransactionProductAssociation(Base):
    __tablename__ = "transaction_product_association"
    transaction_id = Column(Integer, ForeignKey("transactions.id"), primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), primary_key=True)
    quantity = Column(Integer, default=1) # Quantity of this specific product in this transaction
    # You might add price_at_transaction if product prices can change

    transaction = relationship("Transaction", back_populates="products")
    product = relationship("Product", back_populates="transactions")


# 採購單主檔模型 (Purchase Order Header)
class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True, index=True)
    po_number = Column(String, unique=True, index=True, nullable=False)  # 採購單號
    purchase_date = Column(Date, nullable=False)  # 採購日期
    expected_delivery_date = Column(Date, nullable=True)  # 預計到貨日

    # 採購人員資訊
    purchaser_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    purchaser = relationship("User", foreign_keys=[purchaser_id])

    # 供應商資訊
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    supplier = relationship("Supplier", foreign_keys=[supplier_id])

    # 狀態和備註
    status = Column(SQLAlchemyEnum(PurchaseOrderStatus), default=PurchaseOrderStatus.DRAFT)
    notes = Column(Text, nullable=True)  # 備註/採購說明

    # 金額相關
    subtotal = Column(Float, default=0.0)  # 小計
    tax_type = Column(SQLAlchemyEnum(TaxType), default=TaxType.INCLUSIVE)  # 稅務類型
    tax_rate = Column(Float, default=0.05)  # 稅率 (預設5%)
    tax_amount = Column(Float, default=0.0)  # 稅額
    total_amount = Column(Float, default=0.0)  # 含稅總額

    # 付款相關
    payment_method = Column(String, nullable=True)  # 付款方式
    payment_status = Column(SQLAlchemyEnum(PaymentStatus), default=PaymentStatus.UNPAID)

    # 時間戳記
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 關聯到採購明細
    items = relationship("PurchaseOrderItem", back_populates="purchase_order", cascade="all, delete-orphan")


# 採購明細模型 (Purchase Order Line Items)
class PurchaseOrderItem(Base):
    __tablename__ = "purchase_order_items"

    id = Column(Integer, primary_key=True, index=True)

    # 關聯到採購單主檔
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False)
    purchase_order = relationship("PurchaseOrder", back_populates="items")

    # 產品資訊
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    product = relationship("Product")

    # 採購明細
    quantity = Column(Integer, nullable=False)  # 數量
    unit_price = Column(Float, nullable=False)  # 單價
    line_total = Column(Float, nullable=False)  # 小計 (數量 × 單價)
    notes = Column(Text, nullable=True)  # 此項商品的特殊說明

    # 時間戳記
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# 入庫單主檔模型 (Goods Receipt Header)
class GoodsReceipt(Base):
    __tablename__ = "goods_receipts"

    id = Column(Integer, primary_key=True, index=True)
    gr_number = Column(String, unique=True, index=True, nullable=False)  # 入庫單號
    receipt_date = Column(Date, nullable=False)  # 入庫日期

    # 關聯採購單
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False)
    purchase_order = relationship("PurchaseOrder", foreign_keys=[purchase_order_id])

    # 倉管人員
    warehouse_staff_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    warehouse_staff = relationship("User", foreign_keys=[warehouse_staff_id])

    # 倉庫資訊
    warehouse_type = Column(SQLAlchemyEnum(WarehouseType), default=WarehouseType.MAIN)
    warehouse_location = Column(String, nullable=True)  # 倉庫位置描述

    # 狀態和備註
    status = Column(SQLAlchemyEnum(GoodsReceiptStatus), default=GoodsReceiptStatus.DRAFT)
    notes = Column(Text, nullable=True)  # 備註

    # 時間戳記
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 關聯到入庫明細
    items = relationship("GoodsReceiptItem", back_populates="goods_receipt", cascade="all, delete-orphan")


# 入庫明細模型 (Goods Receipt Line Items)
class GoodsReceiptItem(Base):
    __tablename__ = "goods_receipt_items"

    id = Column(Integer, primary_key=True, index=True)

    # 關聯到入庫單主檔
    goods_receipt_id = Column(Integer, ForeignKey("goods_receipts.id"), nullable=False)
    goods_receipt = relationship("GoodsReceipt", back_populates="items")

    # 關聯到採購明細
    purchase_order_item_id = Column(Integer, ForeignKey("purchase_order_items.id"), nullable=False)
    purchase_order_item = relationship("PurchaseOrderItem")

    # 產品資訊
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    product = relationship("Product")

    # 數量資訊
    ordered_quantity = Column(Integer, nullable=False)  # 採購數量（唯讀）
    received_quantity = Column(Integer, nullable=False)  # 實到數量

    # 儲位資訊
    storage_location = Column(String, nullable=True)  # 儲位/倉別
    notes = Column(Text, nullable=True)  # 備註（差異原因等）

    # 時間戳記
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# 銷售單主檔模型 (Sales Order Header)
class SalesOrder(Base):
    __tablename__ = "sales_orders"

    id = Column(Integer, primary_key=True, index=True)
    so_number = Column(String, unique=True, index=True, nullable=False)  # 銷售單號
    sales_date = Column(Date, nullable=False)  # 銷售日期

    # 客戶資訊
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    customer = relationship("Customer", foreign_keys=[customer_id])

    # 銷售人員
    salesperson_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    salesperson = relationship("User", foreign_keys=[salesperson_id])

    # 付款和狀態
    payment_term = Column(SQLAlchemyEnum(PaymentTerm), default=PaymentTerm.CASH)
    status = Column(SQLAlchemyEnum(SalesOrderStatus), default=SalesOrderStatus.DRAFT)
    notes = Column(Text, nullable=True)  # 備註

    # 金額相關
    subtotal = Column(Float, default=0.0)  # 小計
    tax_type = Column(SQLAlchemyEnum(TaxType), default=TaxType.INCLUSIVE)  # 稅務類型
    tax_rate = Column(Float, default=0.05)  # 稅率 (預設5%)
    tax_amount = Column(Float, default=0.0)  # 稅額
    discount_rate = Column(Float, default=0.0)  # 折扣率 (0-1)
    discount_amount = Column(Float, default=0.0)  # 折扣金額
    total_amount = Column(Float, default=0.0)  # 實收總額

    # 時間戳記
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 關聯到銷售明細
    items = relationship("SalesOrderItem", back_populates="sales_order", cascade="all, delete-orphan")


# 銷售明細模型 (Sales Order Line Items)
class SalesOrderItem(Base):
    __tablename__ = "sales_order_items"

    id = Column(Integer, primary_key=True, index=True)

    # 關聯到銷售單主檔
    sales_order_id = Column(Integer, ForeignKey("sales_orders.id"), nullable=False)
    sales_order = relationship("SalesOrder", back_populates="items")

    # 產品資訊
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    product = relationship("Product")

    # 銷售明細
    quantity = Column(Integer, nullable=False)  # 數量
    unit_price = Column(Float, nullable=False)  # 單價
    line_total = Column(Float, nullable=False)  # 小計 (數量 × 單價)
    notes = Column(Text, nullable=True)  # 此項商品的特殊說明

    # 時間戳記
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
