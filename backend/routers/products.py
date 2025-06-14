import os
import shutil
import uuid
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from sqlalchemy.orm import Session

from .. import database, models, schemas, security

router = APIRouter(
    prefix="/api/products",
    tags=["Products"],
    dependencies=[Depends(security.get_current_active_user)]
)

# Directory to store product images
PRODUCT_IMAGE_DIR = "backend/static/product_images"
# Ensure this directory exists (the mkdir -p command above handles this for the subtask)
# In a real app, this might be part of app startup or deployment.

def save_product_image(image_file: UploadFile) -> Optional[str]:
    if not image_file:
        return None

    # Ensure the directory exists
    os.makedirs(PRODUCT_IMAGE_DIR, exist_ok=True)

    # Generate a unique filename to prevent overwrites
    filename_ext = os.path.splitext(image_file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{filename_ext}"
    file_path = os.path.join(PRODUCT_IMAGE_DIR, unique_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(image_file.file, buffer)

    # Return the path to be stored in DB (e.g., /static/product_images/filename.jpg)
    # This path will be used by the frontend, assuming static files are served from /static
    return f"/static/product_images/{unique_filename}"

def delete_product_image(image_url: Optional[str]):
    if image_url:
        # Convert URL path back to system file path
        # Assuming image_url is like /static/product_images/filename.jpg
        # and PRODUCT_IMAGE_DIR is backend/static/product_images
        # We need to construct the full path relative to the project root.
        # For example, if image_url is /static/product_images/foo.jpg,
        # and static files are mounted at "static", and PRODUCT_IMAGE_DIR is "backend/static/product_images"
        # then the actual file path is "backend/static/product_images/foo.jpg"

        # Simplification: if image_url starts with /static/, remove it and prepend 'backend'
        if image_url.startswith("/static/"):
            relative_path = image_url[len("/static/"):] # product_images/filename.jpg
            file_path = os.path.join("backend/static", relative_path) # backend/static/product_images/filename.jpg

            # More robustly, use PRODUCT_IMAGE_DIR and extract filename
            # filename = os.path.basename(image_url)
            # file_path = os.path.join(PRODUCT_IMAGE_DIR, filename)

            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    print(f"Deleted image: {file_path}")
                except OSError as e:
                    print(f"Error deleting image {file_path}: {e.strerror}")
            else:
                print(f"Image not found for deletion: {file_path}")


@router.post("/add", response_model=schemas.Product, status_code=status.HTTP_201_CREATED)
async def add_product(
    name: str = Form(...),
    price: float = Form(...),
    category_id: int = Form(...),
    sku: Optional[str] = Form(None),
    stockQuantity: Optional[int] = Form(0),
    description: Optional[str] = Form(None),
    expiryDate: Optional[str] = Form(None), # Handle date string conversion if needed
    image: Optional[UploadFile] = File(None), # Changed to 'image' to match common frontend field name
    db: Session = Depends(database.get_db)
):
    # Validate category exists
    category = db.query(models.Category).filter(models.Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail=f"Category with id {category_id} not found")

    image_url_path = None
    if image:
        image_url_path = save_product_image(image)

    # Convert expiryDate string to datetime object if provided
    expiry_datetime = None
    if expiryDate:
        try:
            expiry_datetime = datetime.fromisoformat(expiryDate)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid expiryDate format. Use ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS).")


    new_product_data = {
        "name": name,
        "price": price,
        "category_id": category_id,
        "sku": sku,
        "stockQuantity": stockQuantity,
        "description": description,
        "expiryDate": expiry_datetime,
        "imageUrl": image_url_path
    }

    new_product = models.Product(**new_product_data)
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product

@router.put("/update", response_model=schemas.Product)
async def update_product(
    id: int = Form(...), # Product ID to update
    name: Optional[str] = Form(None),
    price: Optional[float] = Form(None),
    category_id: Optional[int] = Form(None),
    sku: Optional[str] = Form(None),
    stockQuantity: Optional[int] = Form(None),
    description: Optional[str] = Form(None),
    expiryDate: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(database.get_db)
):
    db_product = db.query(models.Product).filter(models.Product.id == id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")

    update_data = {}
    if name is not None: update_data['name'] = name
    if price is not None: update_data['price'] = price
    if category_id is not None:
        category = db.query(models.Category).filter(models.Category.id == category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail=f"Category with id {category_id} not found")
        update_data['category_id'] = category_id
    if sku is not None: update_data['sku'] = sku
    if stockQuantity is not None: update_data['stockQuantity'] = stockQuantity
    if description is not None: update_data['description'] = description

    if expiryDate is not None:
        try:
            update_data['expiryDate'] = datetime.fromisoformat(expiryDate)
        except ValueError:
            # Allow unsetting expiryDate by passing empty string or handle specific format
            if expiryDate == "":
                update_data['expiryDate'] = None
            else:
                raise HTTPException(status_code=400, detail="Invalid expiryDate format. Use ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS) or empty string to clear.")


    if image:
        # Delete old image if it exists
        if db_product.imageUrl:
            delete_product_image(db_product.imageUrl)
        update_data['imageUrl'] = save_product_image(image)

    for key, value in update_data.items():
        setattr(db_product, key, value)

    db.commit()
    db.refresh(db_product)
    return db_product


@router.get("/all", response_model=List[schemas.Product])
def read_products(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    products = db.query(models.Product).offset(skip).limit(limit).all()
    return products

@router.get("/{id}", response_model=schemas.Product)
def read_product(id: int, db: Session = Depends(database.get_db)):
    db_product = db.query(models.Product).filter(models.Product.id == id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return db_product

@router.delete("/delete/{id}", response_model=schemas.Product)
def delete_product(id: int, db: Session = Depends(database.get_db)):
    from sqlalchemy.orm import joinedload # Import for eager loading
    db_product = db.query(models.Product).options(joinedload(models.Product.category)).filter(models.Product.id == id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    # Check for related transactions (TransactionProductAssociation)
    # This is a soft check; DB constraints should ideally prevent orphaned records if set up.
    associations = db.query(models.TransactionProductAssociation).filter(models.TransactionProductAssociation.product_id == id).count()
    if associations > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete product with ID {id} as it is part of existing transactions. Please remove it from transactions first."
        )

    # Delete the image file if it exists
    if db_product.imageUrl:
        delete_product_image(db_product.imageUrl)

    db.delete(db_product)
    db.commit()
    return db_product
