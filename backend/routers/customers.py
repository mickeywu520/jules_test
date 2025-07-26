from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import database, models, schemas, security # Adjusted imports

router = APIRouter(
    prefix="/api/customers", # This prefix will be used by main.py
    tags=["Customers"],
    dependencies=[Depends(security.get_current_active_user)] # Apply auth to all customer routes
)

@router.post("/add", response_model=schemas.Customer, status_code=status.HTTP_201_CREATED)
def create_customer(customer: schemas.CustomerCreate, db: Session = Depends(database.get_db)):
    # Check if customer with the same customerCode already exists
    db_customer = db.query(models.Customer).filter(models.Customer.customerCode == customer.customerCode).first()
    if db_customer:
        raise HTTPException(status_code=400, detail=f"Customer with code '{customer.customerCode}' already exists")

    # Check if the customer type exists
    db_customer_type = db.query(models.CustomerType).filter(models.CustomerType.id == customer.customer_type_id).first()
    if db_customer_type is None:
        raise HTTPException(status_code=400, detail="Customer type not found")

    new_customer = models.Customer(
        customer_type_id=customer.customer_type_id,
        salesPersonId=customer.salesPersonId,
        salesPersonName=customer.salesPersonName,
        customerCode=customer.customerCode,
        customerName=customer.customerName,
        contactPerson=customer.contactPerson,
        invoiceTitle=customer.invoiceTitle,
        taxId=customer.taxId,
        phoneNumber=customer.phoneNumber,
        faxNumber=customer.faxNumber,
        deliveryAddress=customer.deliveryAddress,
        businessHours=customer.businessHours,
        paymentMethod=customer.paymentMethod,
        paymentCategory=customer.paymentCategory,
        creditLimit=customer.creditLimit
    )
    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)
    return new_customer

@router.get("/all", response_model=List[schemas.Customer])
def read_customers(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    customers = db.query(models.Customer).offset(skip).limit(limit).all()
    return customers

@router.get("/{id}", response_model=schemas.Customer)
def read_customer(id: int, db: Session = Depends(database.get_db)):
    db_customer = db.query(models.Customer).filter(models.Customer.id == id).first()
    if db_customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return db_customer

@router.get("/code/{customer_code}", response_model=schemas.Customer)
def read_customer_by_code(customer_code: str, db: Session = Depends(database.get_db)):
    db_customer = db.query(models.Customer).filter(models.Customer.customerCode == customer_code).first()
    if db_customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return db_customer

@router.put("/update/{id}", response_model=schemas.Customer)
def update_customer(id: int, customer_update: schemas.CustomerUpdate, db: Session = Depends(database.get_db)):
    db_customer = db.query(models.Customer).filter(models.Customer.id == id).first()
    if db_customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Check if another customer with the new customerCode already exists (if customerCode is being updated)
    if customer_update.customerCode and customer_update.customerCode != db_customer.customerCode:
        existing_customer_with_new_code = db.query(models.Customer).filter(models.Customer.customerCode == customer_update.customerCode).first()
        if existing_customer_with_new_code:
            raise HTTPException(status_code=400, detail=f"Customer with code '{customer_update.customerCode}' already exists")

    # Check if the customer type exists (if customer_type_id is being updated)
    if customer_update.customer_type_id is not None:
        db_customer_type = db.query(models.CustomerType).filter(models.CustomerType.id == customer_update.customer_type_id).first()
        if db_customer_type is None:
            raise HTTPException(status_code=400, detail="Customer type not found")

    # Update fields if provided
    update_data = customer_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_customer, field, value)

    db.commit()
    db.refresh(db_customer)
    return db_customer

@router.delete("/delete/{id}", response_model=schemas.Customer)
def delete_customer(id: int, db: Session = Depends(database.get_db)):
    db_customer = db.query(models.Customer).filter(models.Customer.id == id).first()
    if db_customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Optional: Check for related transactions before deleting
    # You might want to prevent deletion if there are associated transactions
    # For now, direct delete. Add constraints in DB or checks here if needed.

    db.delete(db_customer)
    db.commit()
    return db_customer

# Additional endpoint to search customers by name
@router.get("/search/{search_term}", response_model=List[schemas.Customer])
def search_customers(search_term: str, db: Session = Depends(database.get_db)):
    customers = db.query(models.Customer).filter(
        models.Customer.customerName.ilike(f"%{search_term}%")
    ).all()
    return customers
