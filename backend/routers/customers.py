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

# Additional endpoint to get the next customer code for a specific customer type
@router.get("/next-code/{customer_type_id}")
def get_next_customer_code(customer_type_id: int, db: Session = Depends(database.get_db)):
    # Get the customer type to determine the prefix
    customer_type = db.query(models.CustomerType).filter(models.CustomerType.id == customer_type_id).first()
    if not customer_type:
        raise HTTPException(status_code=404, detail="Customer type not found")
    
    print(f"Customer type ID: {customer_type_id}")
    print(f"Customer type name: {customer_type.type_name}")
    
    # Define the prefix mapping according to user requirements
    prefix_mapping = {
        "連鎖體系": "AA",
        "㇐般月結店家": "B",
        "㇐般下收店家": "D",
        "零售": "X"
    }
    
    # Get the prefix for the customer type
    prefix = prefix_mapping.get(customer_type.type_name, "CUS")
    print(f"Prefix for customer type: {prefix}")
    
    # Find the maximum customer code for this prefix
    # For "連鎖體系" (AA), we need to match codes that start with "AA" followed by 4 digits
    # For others (B, D, X), we need to match codes that start with the prefix followed by 4 digits
    if prefix == "AA":
        # For AA prefix, we need to find codes that match "AA" followed by exactly 4 digits
        max_code = db.query(models.Customer.customerCode).filter(
            models.Customer.customerCode.like("AA____")  # AA followed by exactly 4 characters
        ).order_by(models.Customer.customerCode.desc()).first()
    else:
        # For other prefixes (B, D, X), we need to find codes that match the prefix followed by exactly 4 digits
        max_code = db.query(models.Customer.customerCode).filter(
            models.Customer.customerCode.like(f"{prefix}____")  # Prefix followed by exactly 4 characters
        ).order_by(models.Customer.customerCode.desc()).first()
    
    print(f"Max code found: {max_code}")
    
    # Extract the number part and increment it
    if max_code:
        try:
            # Extract the number part after the prefix
            if prefix == "AA":
                # For "AA", extract the 4 digits after "AA"
                number_part = max_code[0][2:]  # Skip "AA"
            else:
                # For others, extract the 4 digits after the single letter prefix
                number_part = max_code[0][1:]  # Skip the first character
            next_number = int(number_part) + 1
        except (IndexError, ValueError):
            # If there's an issue with parsing, start from 1
            next_number = 1
    else:
        # If no existing code, start from 1
        next_number = 1
    
    print(f"Next number: {next_number}")
    
    # Format the next code with leading zeros (4 digits)
    if prefix == "AA":
        # For "AA", format as "AA" followed by 4 digits
        next_code = f"AA{next_number:04d}"
    else:
        # For others, format as the prefix followed by 4 digits
        next_code = f"{prefix}{next_number:04d}"
    
    print(f"Next code: {next_code}")
    
    return {"next_code": next_code}
