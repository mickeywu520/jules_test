from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import extract, and_

from .. import database, models, schemas, security

router = APIRouter(
    prefix="/api/transactions",
    tags=["Transactions"],
    dependencies=[Depends(security.get_current_active_user)]
)

# Helper function to process products in a transaction (purchase or sell)
def _process_transaction_products(
    db: Session,
    products_involved: List[schemas.TransactionProductAssociationCreate],
    transaction_type: schemas.TransactionType,
    transaction_id: Optional[int] = None # Needed if creating associations for an existing transaction
):
    associations = []
    calculated_total_price = 0.0
    calculated_total_products = 0

    for prod_assoc_data in products_involved:
        db_product = db.query(models.Product).filter(models.Product.id == prod_assoc_data.product_id).first()
        if not db_product:
            raise HTTPException(status_code=404, detail=f"Product with ID {prod_assoc_data.product_id} not found.")

        if transaction_type == schemas.TransactionType.SELL:
            if db_product.stockQuantity < prod_assoc_data.quantity:
                raise HTTPException(status_code=400, detail=f"Not enough stock for product {db_product.name} (ID: {db_product.id}). Available: {db_product.stockQuantity}, Requested: {prod_assoc_data.quantity}")
            db_product.stockQuantity -= prod_assoc_data.quantity
        elif transaction_type == schemas.TransactionType.PURCHASE:
            db_product.stockQuantity += prod_assoc_data.quantity

        db.add(db_product) # Add product to session to save stockQuantity changes

        # Create association - if transaction_id is provided, it means we are adding to an existing transaction
        # For new transactions, transaction_id will be set after the main transaction record is created.
        association_data = {
            "product_id": prod_assoc_data.product_id,
            "quantity": prod_assoc_data.quantity
        }
        if transaction_id:
            association_data["transaction_id"] = transaction_id

        # Store association data to be created after transaction is committed (if new) or add directly
        associations.append(association_data)

        calculated_total_price += db_product.price * prod_assoc_data.quantity
        calculated_total_products += prod_assoc_data.quantity

    return associations, calculated_total_price, calculated_total_products


def _convert_purchase_order_to_transaction(purchase_order: models.PurchaseOrder, db: Session) -> models.Transaction:
    """將採購單轉換為 Transaction 格式"""
    # 計算總產品數量和總價格
    total_products = sum(item.quantity for item in purchase_order.items)
    total_price = purchase_order.total_amount

    # 創建虛擬的 Transaction 物件
    transaction = models.Transaction(
        id=purchase_order.id * 1000000 + 1,  # 使用大數字避免與原有 Transaction ID 衝突
        totalProducts=total_products,
        totalPrice=total_price,
        transactionType=models.TransactionType.PURCHASE,
        transactionStatus=models.TransactionStatus.COMPLETED,
        description=f"採購單: {purchase_order.po_number}",
        note=purchase_order.notes,
        createdAt=purchase_order.created_at,
        updatedAt=purchase_order.updated_at,
        user_id=purchase_order.purchaser_id,
        supplier_id=purchase_order.supplier_id
    )

    # 設置關聯資料
    transaction.user = purchase_order.purchaser
    transaction.supplier = purchase_order.supplier

    # 轉換產品關聯
    transaction.products = []
    for item in purchase_order.items:
        assoc = models.TransactionProductAssociation(
            transaction_id=transaction.id,
            product_id=item.product_id,
            quantity=item.quantity
        )
        assoc.product = item.product
        transaction.products.append(assoc)

    return transaction


def _convert_sales_order_to_transaction(sales_order: models.SalesOrder, db: Session) -> models.Transaction:
    """將銷售單轉換為 Transaction 格式"""
    # 計算總產品數量和總價格
    total_products = sum(item.quantity for item in sales_order.items)
    total_price = sales_order.total_amount

    # 創建虛擬的 Transaction 物件
    transaction = models.Transaction(
        id=sales_order.id * 1000000 + 2,  # 使用大數字避免與原有 Transaction ID 衝突
        totalProducts=total_products,
        totalPrice=total_price,
        transactionType=models.TransactionType.SELL,
        transactionStatus=models.TransactionStatus.COMPLETED,
        description=f"銷售單: {sales_order.so_number}",
        note=sales_order.notes,
        createdAt=sales_order.created_at,
        updatedAt=sales_order.updated_at,
        user_id=sales_order.salesperson_id,
        supplier_id=None  # 銷售單沒有供應商
    )

    # 設置關聯資料
    transaction.user = sales_order.salesperson
    transaction.supplier = None

    # 轉換產品關聯
    transaction.products = []
    for item in sales_order.items:
        assoc = models.TransactionProductAssociation(
            transaction_id=transaction.id,
            product_id=item.product_id,
            quantity=item.quantity
        )
        assoc.product = item.product
        transaction.products.append(assoc)

    return transaction


@router.post("/purchase", response_model=schemas.Transaction, status_code=status.HTTP_201_CREATED)
def create_purchase_transaction(
    transaction_data: schemas.TransactionCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    # Process products first to validate stock and calculate totals
    product_associations_data, total_price, total_products = _process_transaction_products(
        db, transaction_data.products_involved, schemas.TransactionType.PURCHASE
    )

    new_transaction = models.Transaction(
        totalProducts=total_products, # Use calculated total products
        totalPrice=total_price,       # Use calculated total price
        transactionType=schemas.TransactionType.PURCHASE,
        transactionStatus=transaction_data.transactionStatus or schemas.TransactionStatus.COMPLETED, # Purchase usually completed
        description=transaction_data.description,
        note=transaction_data.note,
        user_id=current_user.id,
        supplier_id=transaction_data.supplier_id # Supplier is important for purchase
    )

    if not transaction_data.supplier_id:
         raise HTTPException(status_code=400, detail="Supplier ID is required for purchase transactions.")

    db.add(new_transaction)
    db.commit() # Commit to get new_transaction.id
    db.refresh(new_transaction)

    # Now create TransactionProductAssociation records
    for assoc_data in product_associations_data:
        db_assoc = models.TransactionProductAssociation(
            transaction_id=new_transaction.id,
            product_id=assoc_data["product_id"],
            quantity=assoc_data["quantity"]
        )
        db.add(db_assoc)

    db.commit() # Commit associations and product stock updates
    db.refresh(new_transaction) # Refresh to load the 'products' relationship
    return new_transaction


@router.post("/sell", response_model=schemas.Transaction, status_code=status.HTTP_201_CREATED)
def create_sell_transaction(
    transaction_data: schemas.TransactionCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    product_associations_data, total_price, total_products = _process_transaction_products(
        db, transaction_data.products_involved, schemas.TransactionType.SELL
    )

    new_transaction = models.Transaction(
        totalProducts=total_products,
        totalPrice=total_price,
        transactionType=schemas.TransactionType.SELL,
        transactionStatus=transaction_data.transactionStatus or schemas.TransactionStatus.COMPLETED, # Sell usually completed
        description=transaction_data.description,
        note=transaction_data.note,
        user_id=current_user.id,
        supplier_id=transaction_data.supplier_id # Supplier might be null for sell
    )
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)

    for assoc_data in product_associations_data:
        db_assoc = models.TransactionProductAssociation(
            transaction_id=new_transaction.id,
            product_id=assoc_data["product_id"],
            quantity=assoc_data["quantity"]
        )
        db.add(db_assoc)

    db.commit()
    db.refresh(new_transaction)
    return new_transaction


@router.get("/all", response_model=List[schemas.Transaction])
def read_transactions(
    searchText: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db)
):
    """
    獲取所有交易記錄，包括：
    1. 原有的 Transaction 記錄
    2. 已完成的採購單 (RECEIVED 狀態)
    3. 已出貨的銷售單 (SHIPPED 或 DELIVERED 狀態)
    """
    all_transactions = []

    # 1. 獲取原有的 Transaction 記錄
    original_query = db.query(models.Transaction)
    if searchText:
        search_term = f"%{searchText.lower()}%"
        original_query = original_query.join(models.User).outerjoin(models.Supplier).filter(
            models.Transaction.id.cast(str).ilike(search_term) |
            models.Transaction.description.ilike(search_term) |
            models.Transaction.note.ilike(search_term) |
            models.User.name.ilike(search_term) |
            models.User.email.ilike(search_term) |
            models.Supplier.name.ilike(search_term)
        )

    original_transactions = original_query.order_by(models.Transaction.createdAt.desc()).all()
    all_transactions.extend(original_transactions)

    # 2. 獲取已完成的採購單並轉換為 Transaction 格式
    purchase_query = db.query(models.PurchaseOrder).filter(
        models.PurchaseOrder.status == models.PurchaseOrderStatus.RECEIVED
    )
    if searchText:
        search_term = f"%{searchText.lower()}%"
        purchase_query = purchase_query.join(models.User).outerjoin(models.Supplier).filter(
            models.PurchaseOrder.po_number.ilike(search_term) |
            models.PurchaseOrder.notes.ilike(search_term) |
            models.User.name.ilike(search_term) |
            models.User.email.ilike(search_term) |
            models.Supplier.name.ilike(search_term)
        )

    purchase_orders = purchase_query.order_by(models.PurchaseOrder.created_at.desc()).all()

    # 轉換採購單為 Transaction 格式
    for po in purchase_orders:
        transaction_data = _convert_purchase_order_to_transaction(po, db)
        all_transactions.append(transaction_data)

    # 3. 獲取已出貨的銷售單並轉換為 Transaction 格式
    sales_query = db.query(models.SalesOrder).filter(
        models.SalesOrder.status.in_([
            models.SalesOrderStatus.SHIPPED,
            models.SalesOrderStatus.DELIVERED
        ])
    )
    if searchText:
        search_term = f"%{searchText.lower()}%"
        sales_query = sales_query.join(models.User).outerjoin(models.Customer).filter(
            models.SalesOrder.so_number.ilike(search_term) |
            models.SalesOrder.notes.ilike(search_term) |
            models.User.name.ilike(search_term) |
            models.User.email.ilike(search_term) |
            models.Customer.customerName.ilike(search_term)
        )

    sales_orders = sales_query.order_by(models.SalesOrder.created_at.desc()).all()

    # 轉換銷售單為 Transaction 格式
    for so in sales_orders:
        transaction_data = _convert_sales_order_to_transaction(so, db)
        all_transactions.append(transaction_data)

    # 按創建時間排序
    all_transactions.sort(key=lambda x: x.createdAt, reverse=True)

    # 應用分頁
    total_transactions = all_transactions[skip:skip + limit] if limit > 0 else all_transactions[skip:]

    return total_transactions

@router.get("/{id}", response_model=schemas.Transaction)
def read_transaction(id: int, db: Session = Depends(database.get_db)):
    """
    獲取單個交易記錄，支援：
    1. 原有的 Transaction ID (小於 1000000)
    2. 採購單轉換的 Transaction ID (1000000 * po_id + 1)
    3. 銷售單轉換的 Transaction ID (1000000 * so_id + 2)
    """
    # 檢查是否為採購單轉換的 ID
    if id > 1000000 and id % 1000000 == 1:
        po_id = id // 1000000
        purchase_order = db.query(models.PurchaseOrder).filter(
            models.PurchaseOrder.id == po_id,
            models.PurchaseOrder.status == models.PurchaseOrderStatus.RECEIVED
        ).first()
        if purchase_order is None:
            raise HTTPException(status_code=404, detail="Purchase order transaction not found")
        return _convert_purchase_order_to_transaction(purchase_order, db)

    # 檢查是否為銷售單轉換的 ID
    elif id > 1000000 and id % 1000000 == 2:
        so_id = id // 1000000
        sales_order = db.query(models.SalesOrder).filter(
            models.SalesOrder.id == so_id,
            models.SalesOrder.status.in_([
                models.SalesOrderStatus.SHIPPED,
                models.SalesOrderStatus.DELIVERED
            ])
        ).first()
        if sales_order is None:
            raise HTTPException(status_code=404, detail="Sales order transaction not found")
        return _convert_sales_order_to_transaction(sales_order, db)

    # 原有的 Transaction 查詢
    else:
        db_transaction = db.query(models.Transaction).filter(models.Transaction.id == id).first()
        if db_transaction is None:
            raise HTTPException(status_code=404, detail="Transaction not found")
        return db_transaction

@router.put("/update/{id}", response_model=schemas.Transaction)
def update_transaction_status_endpoint( # Renamed to avoid conflict with schema name
    id: int,
    status_update: schemas.TransactionStatusUpdate, # This expects a single 'status' field
    db: Session = Depends(database.get_db)
):
    """
    更新交易狀態，支援：
    1. 原有的 Transaction 記錄 (小於 1000000)
    2. 採購單交易 (1000000 * po_id + 1) - 會更新對應的採購單狀態
    3. 銷售單交易 (1000000 * so_id + 2) - 會更新對應的銷售單狀態
    """

    # 檢查是否為採購單轉換的 ID
    if id > 1000000 and id % 1000000 == 1:
        po_id = id // 1000000
        purchase_order = db.query(models.PurchaseOrder).filter(models.PurchaseOrder.id == po_id).first()
        if purchase_order is None:
            raise HTTPException(status_code=404, detail="Purchase order not found")

        # 將 Transaction 狀態映射到採購單狀態
        if status_update.status == schemas.TransactionStatus.CANCELLED:
            purchase_order.status = models.PurchaseOrderStatus.CANCELLED
        elif status_update.status == schemas.TransactionStatus.COMPLETED:
            purchase_order.status = models.PurchaseOrderStatus.RECEIVED
        else:
            raise HTTPException(status_code=400, detail="Invalid status for purchase order transaction")

        purchase_order.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(purchase_order)
        return _convert_purchase_order_to_transaction(purchase_order, db)

    # 檢查是否為銷售單轉換的 ID
    elif id > 1000000 and id % 1000000 == 2:
        so_id = id // 1000000
        sales_order = db.query(models.SalesOrder).filter(models.SalesOrder.id == so_id).first()
        if sales_order is None:
            raise HTTPException(status_code=404, detail="Sales order not found")

        # 將 Transaction 狀態映射到銷售單狀態
        if status_update.status == schemas.TransactionStatus.CANCELLED:
            sales_order.status = models.SalesOrderStatus.CANCELLED
        elif status_update.status == schemas.TransactionStatus.COMPLETED:
            sales_order.status = models.SalesOrderStatus.DELIVERED
        else:
            raise HTTPException(status_code=400, detail="Invalid status for sales order transaction")

        sales_order.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(sales_order)
        return _convert_sales_order_to_transaction(sales_order, db)

    # 原有的 Transaction 更新邏輯
    else:
        db_transaction = db.query(models.Transaction).filter(models.Transaction.id == id).first()
        if db_transaction is None:
            raise HTTPException(status_code=404, detail="Transaction not found")

        # 處理庫存回滾邏輯（僅適用於原有的 Transaction）
        if db_transaction.transactionStatus == schemas.TransactionStatus.COMPLETED and \
           status_update.status == schemas.TransactionStatus.CANCELLED:
            for assoc in db_transaction.products:
                db_product = db.query(models.Product).filter(models.Product.id == assoc.product_id).first()
                if db_product:
                    if db_transaction.transactionType == schemas.TransactionType.SELL:
                        db_product.stockQuantity += assoc.quantity # Add back stock
                    elif db_transaction.transactionType == schemas.TransactionType.PURCHASE:
                        db_product.stockQuantity -= assoc.quantity # Remove stock
                    db.add(db_product)

        db_transaction.transactionStatus = status_update.status
        db_transaction.updatedAt = datetime.utcnow()
        db.commit()
        db.refresh(db_transaction)
        return db_transaction

@router.get("/by-month-year", response_model=List[schemas.Transaction])
def read_transactions_by_month_year(
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2000, le=datetime.now().year + 5),
    db: Session = Depends(database.get_db)
):
    transactions = db.query(models.Transaction).filter(
        and_(
            extract('month', models.Transaction.createdAt) == month,
            extract('year', models.Transaction.createdAt) == year
        )
    ).order_by(models.Transaction.createdAt.desc()).all()
    return transactions
