from typing import List
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from .. import database, models, schemas, security

router = APIRouter(
    prefix="/api/goods-receipts",
    tags=["Goods Receipts"],
    dependencies=[Depends(security.get_current_active_user)]
)

def generate_gr_number(db: Session) -> str:
    """生成入庫單號，格式：GR-YYYYMMDD-XXX"""
    today = date.today()
    date_str = today.strftime("%Y%m%d")

    # 查詢當天已有的入庫單號
    existing_grs = db.query(models.GoodsReceipt)\
        .filter(models.GoodsReceipt.gr_number.like(f"GR-{date_str}-%"))\
        .order_by(models.GoodsReceipt.gr_number.desc())\
        .first()

    if existing_grs:
        # 提取最後的序號並加1
        last_number = existing_grs.gr_number.split('-')[-1]
        next_number = int(last_number) + 1
        sequence = f"{next_number:03d}"  # 格式化為3位數
    else:
        # 當天第一筆
        sequence = "001"

    return f"GR-{date_str}-{sequence}"

# 新增入庫單
@router.post("/", response_model=schemas.GoodsReceipt, status_code=status.HTTP_201_CREATED)
def create_goods_receipt(
    goods_receipt: schemas.GoodsReceiptCreate, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    # 驗證採購單是否存在且狀態為已確認
    purchase_order = db.query(models.PurchaseOrder)\
        .filter(models.PurchaseOrder.id == goods_receipt.purchase_order_id)\
        .first()
    
    if not purchase_order:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    
    if purchase_order.status not in [models.PurchaseOrderStatus.CONFIRMED, models.PurchaseOrderStatus.RECEIVED]:
        raise HTTPException(
            status_code=400,
            detail="Only confirmed or received purchase orders can be processed for goods receipt"
        )
    
    # 驗證所有採購明細是否存在
    po_item_ids = [item.purchase_order_item_id for item in goods_receipt.items]
    po_items = db.query(models.PurchaseOrderItem)\
        .filter(models.PurchaseOrderItem.id.in_(po_item_ids))\
        .filter(models.PurchaseOrderItem.purchase_order_id == goods_receipt.purchase_order_id)\
        .all()
    
    if len(po_items) != len(po_item_ids):
        raise HTTPException(status_code=404, detail="One or more purchase order items not found")
    
    # 生成入庫單號
    gr_number = generate_gr_number(db)
    
    # 創建入庫單主檔
    new_gr = models.GoodsReceipt(
        gr_number=gr_number,
        receipt_date=goods_receipt.receipt_date,
        purchase_order_id=goods_receipt.purchase_order_id,
        warehouse_staff_id=current_user.id,
        warehouse_type=goods_receipt.warehouse_type,
        warehouse_location=goods_receipt.warehouse_location,
        notes=goods_receipt.notes
    )
    
    db.add(new_gr)
    db.flush()  # 獲取 GR ID
    
    # 創建入庫明細
    for item_data in goods_receipt.items:
        # 找到對應的採購明細
        po_item = next((item for item in po_items if item.id == item_data.purchase_order_item_id), None)
        if not po_item:
            raise HTTPException(status_code=404, detail=f"Purchase order item {item_data.purchase_order_item_id} not found")
        
        gr_item = models.GoodsReceiptItem(
            goods_receipt_id=new_gr.id,
            purchase_order_item_id=item_data.purchase_order_item_id,
            product_id=item_data.product_id,
            ordered_quantity=item_data.ordered_quantity,
            received_quantity=item_data.received_quantity,
            storage_location=item_data.storage_location,
            notes=item_data.notes
        )
        db.add(gr_item)
    
    db.commit()
    db.refresh(new_gr)
    
    return new_gr

# 獲取所有入庫單
@router.get("/", response_model=List[schemas.GoodsReceipt])
def get_goods_receipts(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(database.get_db)
):
    goods_receipts = db.query(models.GoodsReceipt)\
        .options(
            joinedload(models.GoodsReceipt.warehouse_staff),
            joinedload(models.GoodsReceipt.purchase_order),
            joinedload(models.GoodsReceipt.items).joinedload(models.GoodsReceiptItem.product)
        )\
        .offset(skip)\
        .limit(limit)\
        .all()
    return goods_receipts

# 根據 ID 獲取入庫單
@router.get("/{gr_id}", response_model=schemas.GoodsReceipt)
def get_goods_receipt_by_id(gr_id: int, db: Session = Depends(database.get_db)):
    goods_receipt = db.query(models.GoodsReceipt)\
        .options(
            joinedload(models.GoodsReceipt.warehouse_staff),
            joinedload(models.GoodsReceipt.purchase_order),
            joinedload(models.GoodsReceipt.items).joinedload(models.GoodsReceiptItem.product)
        )\
        .filter(models.GoodsReceipt.id == gr_id)\
        .first()
    
    if not goods_receipt:
        raise HTTPException(status_code=404, detail="Goods receipt not found")
    
    return goods_receipt

# 根據採購單 ID 獲取可入庫的採購明細
@router.get("/purchase-order/{po_id}/items", response_model=List[schemas.PurchaseOrderItem])
def get_receivable_items_by_purchase_order(po_id: int, db: Session = Depends(database.get_db)):
    # 檢查採購單是否存在且狀態為已確認
    purchase_order = db.query(models.PurchaseOrder)\
        .filter(models.PurchaseOrder.id == po_id)\
        .first()
    
    if not purchase_order:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    
    if purchase_order.status not in [models.PurchaseOrderStatus.CONFIRMED, models.PurchaseOrderStatus.RECEIVED]:
        raise HTTPException(
            status_code=400,
            detail="Only confirmed or received purchase orders can be processed for goods receipt"
        )
    
    # 獲取採購明細
    po_items = db.query(models.PurchaseOrderItem)\
        .options(joinedload(models.PurchaseOrderItem.product))\
        .filter(models.PurchaseOrderItem.purchase_order_id == po_id)\
        .all()
    
    return po_items

# 更新入庫單
@router.put("/{gr_id}", response_model=schemas.GoodsReceipt)
def update_goods_receipt(
    gr_id: int,
    goods_receipt: schemas.GoodsReceiptUpdate,
    db: Session = Depends(database.get_db)
):
    db_gr = db.query(models.GoodsReceipt).filter(models.GoodsReceipt.id == gr_id).first()
    if not db_gr:
        raise HTTPException(status_code=404, detail="Goods receipt not found")

    # 更新主檔欄位
    update_data = goods_receipt.model_dump(exclude_unset=True, exclude={'items'})
    for key, value in update_data.items():
        setattr(db_gr, key, value)

    # 更新入庫明細
    if goods_receipt.items is not None:
        # 刪除現有的入庫明細
        db.query(models.GoodsReceiptItem)\
          .filter(models.GoodsReceiptItem.goods_receipt_id == gr_id)\
          .delete()

        # 新增更新後的入庫明細
        for item_data in goods_receipt.items:
            # 驗證必要欄位
            if not item_data.purchase_order_item_id or not item_data.product_id:
                raise HTTPException(status_code=400, detail="purchase_order_item_id and product_id are required for items")

            # 找到對應的採購明細來獲取 ordered_quantity
            po_item = db.query(models.PurchaseOrderItem)\
                .filter(models.PurchaseOrderItem.id == item_data.purchase_order_item_id)\
                .first()

            if not po_item:
                raise HTTPException(status_code=404, detail=f"Purchase order item {item_data.purchase_order_item_id} not found")

            gr_item = models.GoodsReceiptItem(
                goods_receipt_id=gr_id,
                purchase_order_item_id=item_data.purchase_order_item_id,
                product_id=item_data.product_id,
                ordered_quantity=po_item.quantity,  # 從採購明細獲取
                received_quantity=item_data.received_quantity if item_data.received_quantity is not None else po_item.quantity,
                storage_location=item_data.storage_location,
                notes=item_data.notes
            )
            db.add(gr_item)

    db.commit()
    db.refresh(db_gr)
    return db_gr

# 刪除入庫單
@router.delete("/{gr_id}")
def delete_goods_receipt(gr_id: int, db: Session = Depends(database.get_db)):
    db_gr = db.query(models.GoodsReceipt).filter(models.GoodsReceipt.id == gr_id).first()
    if not db_gr:
        raise HTTPException(status_code=404, detail="Goods receipt not found")
    
    # 檢查入庫單狀態，只有草稿狀態才能刪除
    if db_gr.status != models.GoodsReceiptStatus.DRAFT:
        raise HTTPException(
            status_code=400, 
            detail="Only draft goods receipts can be deleted"
        )
    
    # 保存要回傳的資料
    gr_data = {
        "id": db_gr.id,
        "gr_number": db_gr.gr_number,
        "status": db_gr.status.value,
        "message": "Goods receipt deleted successfully"
    }
    
    db.delete(db_gr)
    db.commit()
    
    return gr_data

# 更新入庫單狀態
@router.patch("/{gr_id}/status")
def update_goods_receipt_status(
    gr_id: int, 
    status_data: dict, 
    db: Session = Depends(database.get_db)
):
    db_gr = db.query(models.GoodsReceipt).filter(models.GoodsReceipt.id == gr_id).first()
    if not db_gr:
        raise HTTPException(status_code=404, detail="Goods receipt not found")
    
    # 從字典中提取狀態值
    if 'status' in status_data:
        status_value = status_data['status']
    else:
        status_value = status_data
    
    # 驗證狀態值是否有效
    try:
        valid_status = schemas.GoodsReceiptStatus(status_value)

        # ✅ 處理狀態變更的庫存邏輯 - 先保存舊狀態
        old_status = db_gr.status

        # 更新狀態
        db_gr.status = valid_status

        # 如果從非完成狀態變更為已完成，增加庫存
        if old_status != models.GoodsReceiptStatus.COMPLETED and valid_status == models.GoodsReceiptStatus.COMPLETED:
            # 增加產品庫存
            for item in db_gr.items:
                product = db.query(models.Product)\
                    .filter(models.Product.id == item.product_id)\
                    .first()

                if product:
                    # 增加庫存數量
                    product.stock += item.received_quantity
                    db.add(product)

            # 更新採購單狀態為已收貨
            purchase_order = db.query(models.PurchaseOrder)\
                .filter(models.PurchaseOrder.id == db_gr.purchase_order_id)\
                .first()
            if purchase_order:
                purchase_order.status = models.PurchaseOrderStatus.RECEIVED

        # 如果從已完成狀態變更為其他狀態，扣減庫存
        elif old_status == models.GoodsReceiptStatus.COMPLETED and valid_status != models.GoodsReceiptStatus.COMPLETED:
            # 扣減產品庫存（恢復到入庫前狀態）
            for item in db_gr.items:
                product = db.query(models.Product)\
                    .filter(models.Product.id == item.product_id)\
                    .first()

                if product:
                    # 扣減庫存數量，但不能低於0
                    product.stock = max(0, product.stock - item.received_quantity)
                    db.add(product)
        
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {status_value}")
    
    db.commit()
    db.refresh(db_gr)
    
    return {
        "id": db_gr.id,
        "gr_number": db_gr.gr_number,
        "status": db_gr.status.value,
        "message": "Status updated successfully"
    }

# 根據採購單查詢入庫單
@router.get("/by-purchase-order/{po_id}", response_model=List[schemas.GoodsReceipt])
def get_goods_receipts_by_purchase_order(po_id: int, db: Session = Depends(database.get_db)):
    goods_receipts = db.query(models.GoodsReceipt)\
        .options(
            joinedload(models.GoodsReceipt.warehouse_staff),
            joinedload(models.GoodsReceipt.purchase_order),
            joinedload(models.GoodsReceipt.items).joinedload(models.GoodsReceiptItem.product)
        )\
        .filter(models.GoodsReceipt.purchase_order_id == po_id)\
        .all()
    
    return goods_receipts
