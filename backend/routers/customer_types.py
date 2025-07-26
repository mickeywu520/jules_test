from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import database, models, schemas, security

router = APIRouter(
    prefix="/api/customer-types",
    tags=["Customer Types"],
    dependencies=[Depends(security.get_current_active_user)]
)

@router.post("/", response_model=schemas.CustomerType, status_code=status.HTTP_201_CREATED)
def create_customer_type(
    customer_type: schemas.CustomerTypeCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    # 檢查是否已存在相同的客戶類型
    db_customer_type = db.query(models.CustomerType).filter(
        models.CustomerType.type_name == customer_type.type_name
    ).first()
    
    if db_customer_type:
        raise HTTPException(
            status_code=400,
            detail=f"Customer type '{customer_type.type_name}' already exists"
        )
    
    # 創建新的客戶類型
    new_customer_type = models.CustomerType(
        type_name=customer_type.type_name
    )
    
    db.add(new_customer_type)
    db.commit()
    db.refresh(new_customer_type)
    
    return new_customer_type

@router.get("/", response_model=List[schemas.CustomerType])
def read_customer_types(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    customer_types = db.query(models.CustomerType).offset(skip).limit(limit).all()
    return customer_types

@router.get("/{customer_type_id}", response_model=schemas.CustomerType)
def read_customer_type(
    customer_type_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    db_customer_type = db.query(models.CustomerType).filter(
        models.CustomerType.id == customer_type_id
    ).first()
    
    if db_customer_type is None:
        raise HTTPException(status_code=404, detail="Customer type not found")
    
    return db_customer_type

@router.put("/{customer_type_id}", response_model=schemas.CustomerType)
def update_customer_type(
    customer_type_id: int,
    customer_type_update: schemas.CustomerTypeCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    # 檢查要更新的客戶類型是否存在
    db_customer_type = db.query(models.CustomerType).filter(
        models.CustomerType.id == customer_type_id
    ).first()
    
    if db_customer_type is None:
        raise HTTPException(status_code=404, detail="Customer type not found")
    
    # 檢查是否已存在相同的客戶類型名稱
    existing_customer_type = db.query(models.CustomerType).filter(
        models.CustomerType.type_name == customer_type_update.type_name,
        models.CustomerType.id != customer_type_id
    ).first()
    
    if existing_customer_type:
        raise HTTPException(
            status_code=400,
            detail=f"Customer type '{customer_type_update.type_name}' already exists"
        )
    
    # 更新客戶類型
    db_customer_type.type_name = customer_type_update.type_name
    
    db.commit()
    db.refresh(db_customer_type)
    
    return db_customer_type

@router.delete("/{customer_type_id}", response_model=schemas.CustomerType)
def delete_customer_type(
    customer_type_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    # 檢查要刪除的客戶類型是否存在
    db_customer_type = db.query(models.CustomerType).filter(
        models.CustomerType.id == customer_type_id
    ).first()
    
    if db_customer_type is None:
        raise HTTPException(status_code=404, detail="Customer type not found")
    
    # 檢查是否有客戶正在使用這個類型
    associated_customers = db.query(models.Customer).filter(
        models.Customer.customer_type_id == customer_type_id
    ).first()
    
    if associated_customers:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete customer type because it is associated with existing customers"
        )
    
    # 刪除客戶類型
    db.delete(db_customer_type)
    db.commit()
    
    return db_customer_type
