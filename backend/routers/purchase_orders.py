from typing import List
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from .. import database, models, schemas, security

router = APIRouter(
    prefix="/api/purchase-orders",
    tags=["Purchase Orders"],
    dependencies=[Depends(security.get_current_active_user)]
)

def generate_po_number(db: Session) -> str:
    """生成採購單號，格式：PO-YYYYMMDD-XXX"""
    today = date.today()
    date_str = today.strftime("%Y%m%d")

    # 查詢當天已有的採購單號
    existing_pos = db.query(models.PurchaseOrder)\
        .filter(models.PurchaseOrder.po_number.like(f"PO-{date_str}-%"))\
        .order_by(models.PurchaseOrder.po_number.desc())\
        .first()

    if existing_pos:
        # 提取最後的序號並加1
        last_number = existing_pos.po_number.split('-')[-1]
        next_number = int(last_number) + 1
        sequence = f"{next_number:03d}"  # 格式化為3位數
    else:
        # 當天第一筆
        sequence = "001"

    return f"PO-{date_str}-{sequence}"

def calculate_totals(items: List[models.PurchaseOrderItem], tax_rate: float, tax_type: schemas.TaxType):
    """計算採購單總額"""
    subtotal = sum(item.line_total for item in items)
    
    if tax_type == schemas.TaxType.INCLUSIVE:
        # 含稅：總額 = 小計，稅額 = 小計 * 稅率 / (1 + 稅率)
        total_amount = subtotal
        tax_amount = subtotal * tax_rate / (1 + tax_rate)
    elif tax_type == schemas.TaxType.EXCLUSIVE:
        # 未稅：稅額 = 0，總額 = 小計
        tax_amount = 0
        total_amount = subtotal
    else:  # ADDITIONAL
        # 外加稅：稅額 = 小計 * 稅率，總額 = 小計 + 稅額
        tax_amount = subtotal * tax_rate
        total_amount = subtotal + tax_amount
    
    return subtotal, tax_amount, total_amount

# 新增採購單
@router.post("/", response_model=schemas.PurchaseOrder, status_code=status.HTTP_201_CREATED)
def create_purchase_order(
    purchase_order: schemas.PurchaseOrderCreate, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    # 驗證供應商是否存在
    supplier = db.query(models.Supplier).filter(models.Supplier.id == purchase_order.supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    # 驗證所有產品是否存在
    product_ids = [item.product_id for item in purchase_order.items]
    products = db.query(models.Product).filter(models.Product.id.in_(product_ids)).all()
    if len(products) != len(product_ids):
        raise HTTPException(status_code=404, detail="One or more products not found")
    
    # 生成採購單號
    po_number = generate_po_number(db)
    
    # 創建採購單主檔
    new_po = models.PurchaseOrder(
        po_number=po_number,
        purchase_date=purchase_order.purchase_date,
        expected_delivery_date=purchase_order.expected_delivery_date,
        purchaser_id=current_user.id,
        supplier_id=purchase_order.supplier_id,
        notes=purchase_order.notes,
        tax_type=purchase_order.tax_type,
        tax_rate=purchase_order.tax_rate,
        payment_method=purchase_order.payment_method
    )
    
    db.add(new_po)
    db.flush()  # 獲取 PO ID
    
    # 創建採購明細
    po_items = []
    for item_data in purchase_order.items:
        line_total = item_data.quantity * item_data.unit_price
        po_item = models.PurchaseOrderItem(
            purchase_order_id=new_po.id,
            product_id=item_data.product_id,
            quantity=item_data.quantity,
            unit_price=item_data.unit_price,
            line_total=line_total,
            notes=item_data.notes
        )
        po_items.append(po_item)
        db.add(po_item)
    
    # 計算總額
    subtotal, tax_amount, total_amount = calculate_totals(po_items, purchase_order.tax_rate, purchase_order.tax_type)
    
    new_po.subtotal = subtotal
    new_po.tax_amount = tax_amount
    new_po.total_amount = total_amount
    
    db.commit()
    db.refresh(new_po)
    
    return new_po

# 獲取所有採購單
@router.get("/", response_model=List[schemas.PurchaseOrder])
def get_purchase_orders(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(database.get_db)
):
    purchase_orders = db.query(models.PurchaseOrder)\
        .options(
            joinedload(models.PurchaseOrder.purchaser),
            joinedload(models.PurchaseOrder.supplier),
            joinedload(models.PurchaseOrder.items).joinedload(models.PurchaseOrderItem.product)
        )\
        .offset(skip)\
        .limit(limit)\
        .all()
    return purchase_orders

# 根據 ID 獲取採購單
@router.get("/{po_id}", response_model=schemas.PurchaseOrder)
def get_purchase_order_by_id(po_id: int, db: Session = Depends(database.get_db)):
    purchase_order = db.query(models.PurchaseOrder)\
        .options(
            joinedload(models.PurchaseOrder.purchaser),
            joinedload(models.PurchaseOrder.supplier),
            joinedload(models.PurchaseOrder.items).joinedload(models.PurchaseOrderItem.product)
        )\
        .filter(models.PurchaseOrder.id == po_id)\
        .first()
    
    if not purchase_order:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    
    return purchase_order

# 更新採購單
@router.put("/{po_id}", response_model=schemas.PurchaseOrder)
def update_purchase_order(
    po_id: int, 
    purchase_order: schemas.PurchaseOrderUpdate, 
    db: Session = Depends(database.get_db)
):
    db_po = db.query(models.PurchaseOrder).filter(models.PurchaseOrder.id == po_id).first()
    if not db_po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    
    # 如果要更新供應商，檢查供應商是否存在
    if purchase_order.supplier_id:
        supplier = db.query(models.Supplier).filter(models.Supplier.id == purchase_order.supplier_id).first()
        if not supplier:
            raise HTTPException(status_code=404, detail="Supplier not found")
    
    # 更新欄位
    update_data = purchase_order.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_po, key, value)
    
    db.commit()
    db.refresh(db_po)
    return db_po

# 刪除採購單
@router.delete("/{po_id}")
def delete_purchase_order(po_id: int, db: Session = Depends(database.get_db)):
    db_po = db.query(models.PurchaseOrder)\
        .options(
            joinedload(models.PurchaseOrder.purchaser),
            joinedload(models.PurchaseOrder.supplier),
            joinedload(models.PurchaseOrder.items).joinedload(models.PurchaseOrderItem.product)
        )\
        .filter(models.PurchaseOrder.id == po_id)\
        .first()

    if not db_po:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    # 檢查採購單狀態，只有草稿狀態才能刪除
    if db_po.status != models.PurchaseOrderStatus.DRAFT:
        raise HTTPException(
            status_code=400,
            detail="Only draft purchase orders can be deleted"
        )

    # 保存要回傳的資料
    po_data = {
        "id": db_po.id,
        "po_number": db_po.po_number,
        "status": db_po.status.value,
        "message": "Purchase order deleted successfully"
    }

    db.delete(db_po)
    db.commit()

    return po_data

# 更新採購單狀態
@router.patch("/{po_id}/status", response_model=schemas.PurchaseOrder)
def update_purchase_order_status(
    po_id: int,
    status_data: dict,
    db: Session = Depends(database.get_db)
):
    db_po = db.query(models.PurchaseOrder).filter(models.PurchaseOrder.id == po_id).first()
    if not db_po:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    # 從字典中提取狀態值
    if 'status' in status_data:
        status_value = status_data['status']
    else:
        # 如果直接傳送狀態字串
        status_value = status_data

    # 驗證狀態值是否有效
    try:
        valid_status = schemas.PurchaseOrderStatus(status_value)
        db_po.status = valid_status
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {status_value}")

    db.commit()
    db.refresh(db_po)
    return db_po
