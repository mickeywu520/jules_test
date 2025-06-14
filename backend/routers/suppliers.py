from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import database, models, schemas, security

router = APIRouter(
    prefix="/api/suppliers",
    tags=["Suppliers"],
    dependencies=[Depends(security.get_current_active_user)] # Apply auth to all supplier routes
)

@router.post("/add", response_model=schemas.Supplier, status_code=status.HTTP_201_CREATED)
def create_supplier(supplier: schemas.SupplierCreate, db: Session = Depends(database.get_db)):
    # Optional: Check if supplier with the same name already exists
    db_supplier_check = db.query(models.Supplier).filter(models.Supplier.name == supplier.name).first()
    if db_supplier_check:
        raise HTTPException(status_code=400, detail=f"Supplier with name '{supplier.name}' already exists")

    new_supplier = models.Supplier(
        name=supplier.name,
        contactInfo=supplier.contactInfo,
        address=supplier.address
    )
    db.add(new_supplier)
    db.commit()
    db.refresh(new_supplier)
    return new_supplier

@router.get("/all", response_model=List[schemas.Supplier])
def read_suppliers(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    suppliers = db.query(models.Supplier).offset(skip).limit(limit).all()
    return suppliers

@router.get("/{id}", response_model=schemas.Supplier)
def read_supplier(id: int, db: Session = Depends(database.get_db)):
    db_supplier = db.query(models.Supplier).filter(models.Supplier.id == id).first()
    if db_supplier is None:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return db_supplier

@router.put("/update/{id}", response_model=schemas.Supplier)
def update_supplier(id: int, supplier_update: schemas.SupplierCreate, db: Session = Depends(database.get_db)):
    db_supplier = db.query(models.Supplier).filter(models.Supplier.id == id).first()
    if db_supplier is None:
        raise HTTPException(status_code=404, detail="Supplier not found")

    # Optional: Check if another supplier with the new name already exists (and it's not the current one)
    if supplier_update.name != db_supplier.name:
        existing_supplier_with_new_name = db.query(models.Supplier).filter(models.Supplier.name == supplier_update.name).first()
        if existing_supplier_with_new_name:
            raise HTTPException(status_code=400, detail=f"Another supplier with name '{supplier_update.name}' already exists")

    db_supplier.name = supplier_update.name
    db_supplier.contactInfo = supplier_update.contactInfo
    db_supplier.address = supplier_update.address
    db.commit()
    db.refresh(db_supplier)
    return db_supplier

@router.delete("/delete/{id}", response_model=schemas.Supplier)
def delete_supplier(id: int, db: Session = Depends(database.get_db)):
    db_supplier = db.query(models.Supplier).filter(models.Supplier.id == id).first()
    if db_supplier is None:
        raise HTTPException(status_code=404, detail="Supplier not found")

    # Check for related transactions before deleting
    if db_supplier.transactions:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete supplier with associated transactions. Please reassign or delete transactions first."
        )

    db.delete(db_supplier)
    db.commit()
    return db_supplier
