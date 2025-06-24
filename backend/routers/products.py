from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import database, models, schemas, security

router = APIRouter(
    prefix="/api/products",
    tags=["Products"],
    dependencies=[Depends(security.get_current_active_user)]
)

# 新增產品
@router.post("/add", response_model=schemas.Product, status_code=status.HTTP_201_CREATED)
def create_product(product: schemas.ProductCreate, db: Session = Depends(database.get_db)):
    # 檢查產品編號是否已存在（只檢查未刪除的產品）
    db_product = db.query(models.Product)\
        .filter(models.Product.productCode == product.productCode, models.Product.is_deleted == False)\
        .first()
    if db_product:
        raise HTTPException(status_code=400, detail="Product code already exists")

    # 檢查類別是否存在
    category = db.query(models.Category).filter(models.Category.id == product.category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    new_product = models.Product(
        productCode=product.productCode,
        productName=product.productName,
        unit=product.unit,
        warehouse=product.warehouse,
        unitWeight=product.unitWeight,
        barcode=product.barcode,
        category_id=product.category_id
    )

    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product

# 更新產品
@router.put("/update/{id}", response_model=schemas.Product)
def update_product(id: int, product: schemas.ProductUpdate, db: Session = Depends(database.get_db)):
    db_product = db.query(models.Product).filter(models.Product.id == id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")

    # 如果要更新產品編號，檢查是否已存在
    if product.productCode and product.productCode != db_product.productCode:
        existing_product = db.query(models.Product).filter(models.Product.productCode == product.productCode).first()
        if existing_product:
            raise HTTPException(status_code=400, detail="Product code already exists")

    # 如果要更新類別，檢查類別是否存在
    if product.category_id:
        category = db.query(models.Category).filter(models.Category.id == product.category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")

    # 更新欄位
    update_data = product.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_product, key, value)

    db.commit()
    db.refresh(db_product)
    return db_product


# 獲取所有產品（可選擇是否包含已刪除的產品）
@router.get("/all", response_model=List[schemas.Product])
def get_products(
    skip: int = 0,
    limit: int = 100,
    include_deleted: bool = False,
    db: Session = Depends(database.get_db)
):
    query = db.query(models.Product)

    if not include_deleted:
        # 預設只顯示未刪除的產品
        query = query.filter(models.Product.is_deleted == False)

    products = query.offset(skip).limit(limit).all()
    return products

# 獲取有效產品（只用於銷售單等業務邏輯）
@router.get("/active", response_model=List[schemas.Product])
def get_active_products(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    products = db.query(models.Product)\
        .filter(models.Product.is_deleted == False)\
        .offset(skip).limit(limit).all()
    return products

# 根據 ID 獲取產品（只顯示未刪除的產品）
@router.get("/{id}", response_model=schemas.Product)
def get_product_by_id(id: int, db: Session = Depends(database.get_db)):
    db_product = db.query(models.Product)\
        .filter(models.Product.id == id, models.Product.is_deleted == False)\
        .first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return db_product

# 軟刪除產品
@router.delete("/delete/{id}", response_model=schemas.Product)
def delete_product(id: int, db: Session = Depends(database.get_db)):
    # 只查詢未刪除的產品
    db_product = db.query(models.Product)\
        .filter(models.Product.id == id, models.Product.is_deleted == False)\
        .first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    # 檢查產品是否已經被刪除
    if db_product.is_deleted:
        raise HTTPException(status_code=400, detail="Product already deleted")

    # 軟刪除：標記為已刪除，不實際刪除記錄
    from datetime import datetime
    db_product.is_deleted = True
    db_product.deleted_at = datetime.utcnow()
    # TODO: 如果有當前用戶資訊，可以設定 deleted_by
    # db_product.deleted_by = current_user.id

    db.commit()
    db.refresh(db_product)
    return db_product

# 恢復已刪除的產品（可選功能）
@router.patch("/restore/{id}", response_model=schemas.Product)
def restore_product(id: int, db: Session = Depends(database.get_db)):
    # 查詢已刪除的產品
    db_product = db.query(models.Product)\
        .filter(models.Product.id == id, models.Product.is_deleted == True)\
        .first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Deleted product not found")

    # 檢查產品編號是否與現有未刪除產品衝突
    existing_product = db.query(models.Product)\
        .filter(models.Product.productCode == db_product.productCode, models.Product.is_deleted == False)\
        .first()
    if existing_product:
        raise HTTPException(status_code=400, detail="Cannot restore: product code already exists")

    # 恢復產品
    db_product.is_deleted = False
    db_product.deleted_at = None
    db_product.deleted_by = None

    db.commit()
    db.refresh(db_product)
    return db_product

# 獲取已刪除的產品列表（管理員功能）
@router.get("/deleted/all", response_model=List[schemas.Product])
def get_deleted_products(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    products = db.query(models.Product)\
        .filter(models.Product.is_deleted == True)\
        .offset(skip).limit(limit).all()
    return products
