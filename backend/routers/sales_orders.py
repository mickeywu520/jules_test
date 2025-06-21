from typing import List
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from .. import database, models, schemas, security

router = APIRouter(
    prefix="/api/sales-orders",
    tags=["Sales Orders"],
    dependencies=[Depends(security.get_current_active_user)]
)

def generate_so_number(db: Session) -> str:
    """生成銷售單號，格式：SO-YYYYMMDD-XXX"""
    today = date.today()
    date_str = today.strftime("%Y%m%d")

    # 查詢當天已有的銷售單號
    existing_sos = db.query(models.SalesOrder)\
        .filter(models.SalesOrder.so_number.like(f"SO-{date_str}-%"))\
        .order_by(models.SalesOrder.so_number.desc())\
        .first()

    if existing_sos:
        # 提取最後的序號並加1
        last_number = existing_sos.so_number.split('-')[-1]
        next_number = int(last_number) + 1
        sequence = f"{next_number:03d}"  # 格式化為3位數
    else:
        # 當天第一筆
        sequence = "001"

    return f"SO-{date_str}-{sequence}"

def deduct_inventory(db: Session, sales_order_items: List[dict]) -> None:
    """扣減庫存"""
    for item_data in sales_order_items:
        product = db.query(models.Product)\
            .filter(models.Product.id == item_data['product_id'])\
            .first()

        if product:
            # 扣減庫存
            product.stock = max(0, product.stock - item_data['quantity'])
            db.add(product)

def restore_inventory(db: Session, sales_order_items: List[dict]) -> None:
    """恢復庫存（用於取消銷售單時）"""
    for item_data in sales_order_items:
        product = db.query(models.Product)\
            .filter(models.Product.id == item_data['product_id'])\
            .first()

        if product:
            # 恢復庫存
            product.stock += item_data['quantity']
            db.add(product)

def calculate_sales_order_totals(sales_order_data: dict, items: List[dict]) -> dict:
    """計算銷售單總金額"""
    # 計算小計
    subtotal = sum(item['line_total'] for item in items)
    
    # 計算折扣金額
    discount_rate = sales_order_data.get('discount_rate', 0.0)
    discount_amount = subtotal * discount_rate
    
    # 計算稅額
    tax_rate = sales_order_data.get('tax_rate', 0.05)
    tax_type = sales_order_data.get('tax_type', 'INCLUSIVE')
    
    if tax_type == 'INCLUSIVE':
        # 含稅：稅額 = (小計 - 折扣) / (1 + 稅率) * 稅率
        tax_base = subtotal - discount_amount
        tax_amount = tax_base / (1 + tax_rate) * tax_rate
        total_amount = subtotal - discount_amount
    elif tax_type == 'EXCLUSIVE':
        # 未稅：稅額 = (小計 - 折扣) * 稅率
        tax_base = subtotal - discount_amount
        tax_amount = tax_base * tax_rate
        total_amount = subtotal - discount_amount + tax_amount
    else:  # ADDITIONAL
        # 外加稅：稅額 = (小計 - 折扣) * 稅率
        tax_base = subtotal - discount_amount
        tax_amount = tax_base * tax_rate
        total_amount = subtotal - discount_amount + tax_amount
    
    return {
        'subtotal': round(subtotal, 2),
        'discount_amount': round(discount_amount, 2),
        'tax_amount': round(tax_amount, 2),
        'total_amount': round(total_amount, 2)
    }

# 新增銷售單
@router.post("/", response_model=schemas.SalesOrder, status_code=status.HTTP_201_CREATED)
def create_sales_order(
    sales_order: schemas.SalesOrderCreate, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    # 驗證客戶是否存在
    customer = db.query(models.Customer)\
        .filter(models.Customer.id == sales_order.customer_id)\
        .first()
    
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # 驗證所有產品是否存在並檢查庫存
    product_ids = [item.product_id for item in sales_order.items]
    products = db.query(models.Product)\
        .filter(models.Product.id.in_(product_ids))\
        .all()

    if len(products) != len(product_ids):
        raise HTTPException(status_code=404, detail="One or more products not found")

    # 檢查庫存是否足夠
    for item_data in sales_order.items:
        product = next((p for p in products if p.id == item_data.product_id), None)
        if product and item_data.quantity > product.stock:
            raise HTTPException(
                status_code=400,
                detail=f"Product '{product.productName}' insufficient stock. Available: {product.stock}, Required: {item_data.quantity}"
            )
    
    # 準備明細資料並計算小計
    items_data = []
    for item_data in sales_order.items:
        line_total = item_data.quantity * item_data.unit_price
        items_data.append({
            'product_id': item_data.product_id,
            'quantity': item_data.quantity,
            'unit_price': item_data.unit_price,
            'line_total': line_total,
            'notes': item_data.notes
        })
    
    # 計算總金額
    totals = calculate_sales_order_totals(sales_order.model_dump(), items_data)
    
    # 生成銷售單號
    so_number = generate_so_number(db)
    
    # 創建銷售單主檔
    new_so = models.SalesOrder(
        so_number=so_number,
        sales_date=sales_order.sales_date,
        customer_id=sales_order.customer_id,
        salesperson_id=current_user.id,
        payment_term=sales_order.payment_term,
        notes=sales_order.notes,
        tax_type=sales_order.tax_type,
        tax_rate=sales_order.tax_rate,
        discount_rate=sales_order.discount_rate,
        **totals
    )
    
    db.add(new_so)
    db.flush()  # 獲取 SO ID
    
    # 創建銷售明細
    for item_data in items_data:
        so_item = models.SalesOrderItem(
            sales_order_id=new_so.id,
            **item_data
        )
        db.add(so_item)
    
    db.commit()
    db.refresh(new_so)
    
    return new_so

# 獲取所有銷售單
@router.get("/", response_model=List[schemas.SalesOrder])
def get_sales_orders(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(database.get_db)
):
    sales_orders = db.query(models.SalesOrder)\
        .options(
            joinedload(models.SalesOrder.salesperson),
            joinedload(models.SalesOrder.customer),
            joinedload(models.SalesOrder.items).joinedload(models.SalesOrderItem.product)
        )\
        .offset(skip)\
        .limit(limit)\
        .all()
    return sales_orders

# 根據 ID 獲取銷售單
@router.get("/{so_id}", response_model=schemas.SalesOrder)
def get_sales_order_by_id(so_id: int, db: Session = Depends(database.get_db)):
    sales_order = db.query(models.SalesOrder)\
        .options(
            joinedload(models.SalesOrder.salesperson),
            joinedload(models.SalesOrder.customer),
            joinedload(models.SalesOrder.items).joinedload(models.SalesOrderItem.product)
        )\
        .filter(models.SalesOrder.id == so_id)\
        .first()
    
    if not sales_order:
        raise HTTPException(status_code=404, detail="Sales order not found")
    
    return sales_order

# 更新銷售單
@router.put("/{so_id}", response_model=schemas.SalesOrder)
def update_sales_order(
    so_id: int, 
    sales_order: schemas.SalesOrderUpdate, 
    db: Session = Depends(database.get_db)
):
    db_so = db.query(models.SalesOrder).filter(models.SalesOrder.id == so_id).first()
    if not db_so:
        raise HTTPException(status_code=404, detail="Sales order not found")
    
    # 更新主檔欄位
    update_data = sales_order.model_dump(exclude_unset=True, exclude={'items'})
    for key, value in update_data.items():
        setattr(db_so, key, value)
    
    # 更新銷售明細
    if sales_order.items is not None:
        # 刪除現有的銷售明細
        db.query(models.SalesOrderItem)\
          .filter(models.SalesOrderItem.sales_order_id == so_id)\
          .delete()
        
        # 準備明細資料並計算小計
        items_data = []
        for item_data in sales_order.items:
            if not item_data.product_id:
                raise HTTPException(status_code=400, detail="product_id is required for items")
            
            line_total = item_data.quantity * item_data.unit_price
            items_data.append({
                'product_id': item_data.product_id,
                'quantity': item_data.quantity,
                'unit_price': item_data.unit_price,
                'line_total': line_total,
                'notes': item_data.notes
            })
        
        # 重新計算總金額
        current_data = {
            'discount_rate': getattr(db_so, 'discount_rate', 0.0),
            'tax_rate': getattr(db_so, 'tax_rate', 0.05),
            'tax_type': getattr(db_so, 'tax_type', 'INCLUSIVE')
        }
        totals = calculate_sales_order_totals(current_data, items_data)
        
        # 更新總金額
        for key, value in totals.items():
            setattr(db_so, key, value)
        
        # 新增更新後的銷售明細
        for item_data in items_data:
            so_item = models.SalesOrderItem(
                sales_order_id=so_id,
                **item_data
            )
            db.add(so_item)
    
    db.commit()
    db.refresh(db_so)
    return db_so

# 刪除銷售單
@router.delete("/{so_id}")
def delete_sales_order(so_id: int, db: Session = Depends(database.get_db)):
    db_so = db.query(models.SalesOrder).filter(models.SalesOrder.id == so_id).first()
    if not db_so:
        raise HTTPException(status_code=404, detail="Sales order not found")
    
    # 檢查銷售單狀態，只有草稿狀態才能刪除
    if db_so.status != models.SalesOrderStatus.DRAFT:
        raise HTTPException(
            status_code=400, 
            detail="Only draft sales orders can be deleted"
        )
    
    # 保存要回傳的資料
    so_data = {
        "id": db_so.id,
        "so_number": db_so.so_number,
        "status": db_so.status.value,
        "message": "Sales order deleted successfully"
    }
    
    db.delete(db_so)
    db.commit()
    
    return so_data

# 更新銷售單狀態
@router.patch("/{so_id}/status")
def update_sales_order_status(
    so_id: int,
    status_data: dict,
    db: Session = Depends(database.get_db)
):
    db_so = db.query(models.SalesOrder)\
        .options(joinedload(models.SalesOrder.items))\
        .filter(models.SalesOrder.id == so_id)\
        .first()

    if not db_so:
        raise HTTPException(status_code=404, detail="Sales order not found")

    # 從字典中提取狀態值
    if 'status' in status_data:
        status_value = status_data['status']
    else:
        status_value = status_data

    # 驗證狀態值是否有效
    try:
        old_status = db_so.status
        valid_status = schemas.SalesOrderStatus(status_value)

        # 檢查狀態變更邏輯
        if old_status == models.SalesOrderStatus.CONFIRMED and valid_status == models.SalesOrderStatus.SHIPPED:
            # 從已確認變更為已出貨：扣減庫存
            items_data = []
            for item in db_so.items:
                # 再次檢查庫存是否足夠
                product = db.query(models.Product)\
                    .filter(models.Product.id == item.product_id)\
                    .first()

                if product and item.quantity > product.stock:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Product '{product.productName}' insufficient stock. Available: {product.stock}, Required: {item.quantity}"
                    )

                items_data.append({
                    'product_id': item.product_id,
                    'quantity': item.quantity
                })

            # 扣減庫存
            deduct_inventory(db, items_data)

        elif old_status == models.SalesOrderStatus.SHIPPED and valid_status == models.SalesOrderStatus.CANCELLED:
            # 從已出貨變更為已取消：恢復庫存
            items_data = []
            for item in db_so.items:
                items_data.append({
                    'product_id': item.product_id,
                    'quantity': item.quantity
                })

            # 恢復庫存
            restore_inventory(db, items_data)

        db_so.status = valid_status

    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {status_value}")

    db.commit()
    db.refresh(db_so)

    return {
        "id": db_so.id,
        "so_number": db_so.so_number,
        "status": db_so.status.value,
        "message": "Status updated successfully"
    }
