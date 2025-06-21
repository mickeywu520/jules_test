from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLAlchemyEnum, Text
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

class CustomerType(str, enum.Enum):
    INDIVIDUAL = "INDIVIDUAL"  # 個人客戶
    COMPANY = "COMPANY"        # 公司客戶
    GOVERNMENT = "GOVERNMENT"  # 政府機關
    OTHER = "OTHER"           # 其他

class PaymentMethod(str, enum.Enum):
    CASH = "CASH"             # 現金
    CREDIT_CARD = "CREDIT_CARD"  # 信用卡
    BANK_TRANSFER = "BANK_TRANSFER"  # 銀行轉帳
    CHECK = "CHECK"           # 支票
    MONTHLY_PAYMENT = "MONTHLY_PAYMENT"  # 月結
    OTHER = "OTHER"           # 其他

class PaymentCategory(str, enum.Enum):
    PREPAID = "PREPAID"       # 預付
    CASH_ON_DELIVERY = "CASH_ON_DELIVERY"  # 貨到付款
    CREDIT = "CREDIT"         # 賒帳
    MONTHLY_SETTLEMENT = "MONTHLY_SETTLEMENT"  # 月結
    OTHER = "OTHER"           # 其他

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

# Category Model
class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)

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
    customerType = Column(SQLAlchemyEnum(CustomerType), nullable=False)  # 客戶類型
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
    paymentMethod = Column(SQLAlchemyEnum(PaymentMethod), nullable=True)  # 收款方式
    paymentCategory = Column(SQLAlchemyEnum(PaymentCategory), nullable=True)  # 收款類別
    creditLimit = Column(Float, nullable=True, default=0.0)  # 銷貨額度
    updatedAt = Column(DateTime(timezone=True), onupdate=func.now())

    # 可以添加與交易的關聯（如果需要的話）
    # transactions = relationship("Transaction", back_populates="customer")

# Product Model
class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    sku = Column(String, unique=True, index=True, nullable=True) # SKU might be optional or unique
    price = Column(Float, nullable=False)
    stockQuantity = Column(Integer, default=0)
    description = Column(Text, nullable=True)
    expiryDate = Column(DateTime, nullable=True) # Assuming this can be null
    imageUrl = Column(String, nullable=True) # Path to image or URL
    createdAt = Column(DateTime(timezone=True), server_default=func.now())

    category_id = Column(Integer, ForeignKey("categories.id"))
    category = relationship("Category", back_populates="products")

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
