from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import database, models, schemas, security # Adjusted imports

router = APIRouter(
    prefix="/api/categories", # This prefix will be used by main.py
    tags=["Categories"],
    dependencies=[Depends(security.get_current_active_user)] # Apply auth to all category routes
)

@router.post("/add", response_model=schemas.Category, status_code=status.HTTP_201_CREATED)
def create_category(category: schemas.CategoryCreate, db: Session = Depends(database.get_db)):
    # Check if category with the same name already exists
    db_category = db.query(models.Category).filter(models.Category.name == category.name).first()
    if db_category:
        raise HTTPException(status_code=400, detail=f"Category with name '{category.name}' already exists")

    new_category = models.Category(name=category.name)
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category

@router.get("/all", response_model=List[schemas.Category])
def read_categories(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    categories = db.query(models.Category).offset(skip).limit(limit).all()
    return categories

@router.get("/{id}", response_model=schemas.Category)
def read_category(id: int, db: Session = Depends(database.get_db)):
    db_category = db.query(models.Category).filter(models.Category.id == id).first()
    if db_category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return db_category

@router.put("/update/{id}", response_model=schemas.Category)
def update_category(id: int, category_update: schemas.CategoryCreate, db: Session = Depends(database.get_db)):
    db_category = db.query(models.Category).filter(models.Category.id == id).first()
    if db_category is None:
        raise HTTPException(status_code=404, detail="Category not found")

    # Check if another category with the new name already exists (and it's not the current one)
    if category_update.name != db_category.name:
        existing_category_with_new_name = db.query(models.Category).filter(models.Category.name == category_update.name).first()
        if existing_category_with_new_name:
            raise HTTPException(status_code=400, detail=f"Category with name '{category_update.name}' already exists")

    db_category.name = category_update.name
    db.commit()
    db.refresh(db_category)
    return db_category

@router.delete("/delete/{id}", response_model=schemas.Category) # Or return a status code like 204 No Content
def delete_category(id: int, db: Session = Depends(database.get_db)):
    db_category = db.query(models.Category).filter(models.Category.id == id).first()
    if db_category is None:
        raise HTTPException(status_code=404, detail="Category not found")

    # Check for related products before deleting (optional, depends on desired referential integrity handling)
    # If products are associated, you might want to prevent deletion or handle it (e.g., set product.category_id to null or delete products)
    # For now, direct delete. Add constraints in DB or checks here if needed.
    if db_category.products:
         raise HTTPException(
            status_code=400,
            detail="Cannot delete category with associated products. Please reassign or delete products first."
        )

    db.delete(db_category)
    db.commit()
    # return {"message": "Category deleted successfully"} # Alternative response
    return db_category # Returning the deleted object can be useful
