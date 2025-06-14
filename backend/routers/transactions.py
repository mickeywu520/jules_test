from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import extract, and_

from .. import database, models, schemas, security

router = APIRouter(
    prefix="/api/transactions",
    tags=["Transactions"],
    dependencies=[Depends(security.get_current_active_user)]
)

# Helper function to process products in a transaction (purchase or sell)
def _process_transaction_products(
    db: Session,
    products_involved: List[schemas.TransactionProductAssociationCreate],
    transaction_type: schemas.TransactionType,
    transaction_id: Optional[int] = None # Needed if creating associations for an existing transaction
):
    associations = []
    calculated_total_price = 0.0
    calculated_total_products = 0

    for prod_assoc_data in products_involved:
        db_product = db.query(models.Product).filter(models.Product.id == prod_assoc_data.product_id).first()
        if not db_product:
            raise HTTPException(status_code=404, detail=f"Product with ID {prod_assoc_data.product_id} not found.")

        if transaction_type == schemas.TransactionType.SELL:
            if db_product.stockQuantity < prod_assoc_data.quantity:
                raise HTTPException(status_code=400, detail=f"Not enough stock for product {db_product.name} (ID: {db_product.id}). Available: {db_product.stockQuantity}, Requested: {prod_assoc_data.quantity}")
            db_product.stockQuantity -= prod_assoc_data.quantity
        elif transaction_type == schemas.TransactionType.PURCHASE:
            db_product.stockQuantity += prod_assoc_data.quantity

        db.add(db_product) # Add product to session to save stockQuantity changes

        # Create association - if transaction_id is provided, it means we are adding to an existing transaction
        # For new transactions, transaction_id will be set after the main transaction record is created.
        association_data = {
            "product_id": prod_assoc_data.product_id,
            "quantity": prod_assoc_data.quantity
        }
        if transaction_id:
            association_data["transaction_id"] = transaction_id

        # Store association data to be created after transaction is committed (if new) or add directly
        associations.append(association_data)

        calculated_total_price += db_product.price * prod_assoc_data.quantity
        calculated_total_products += prod_assoc_data.quantity

    return associations, calculated_total_price, calculated_total_products


@router.post("/purchase", response_model=schemas.Transaction, status_code=status.HTTP_201_CREATED)
def create_purchase_transaction(
    transaction_data: schemas.TransactionCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    # Process products first to validate stock and calculate totals
    product_associations_data, total_price, total_products = _process_transaction_products(
        db, transaction_data.products_involved, schemas.TransactionType.PURCHASE
    )

    new_transaction = models.Transaction(
        totalProducts=total_products, # Use calculated total products
        totalPrice=total_price,       # Use calculated total price
        transactionType=schemas.TransactionType.PURCHASE,
        transactionStatus=transaction_data.transactionStatus or schemas.TransactionStatus.COMPLETED, # Purchase usually completed
        description=transaction_data.description,
        note=transaction_data.note,
        user_id=current_user.id,
        supplier_id=transaction_data.supplier_id # Supplier is important for purchase
    )

    if not transaction_data.supplier_id:
         raise HTTPException(status_code=400, detail="Supplier ID is required for purchase transactions.")

    db.add(new_transaction)
    db.commit() # Commit to get new_transaction.id
    db.refresh(new_transaction)

    # Now create TransactionProductAssociation records
    for assoc_data in product_associations_data:
        db_assoc = models.TransactionProductAssociation(
            transaction_id=new_transaction.id,
            product_id=assoc_data["product_id"],
            quantity=assoc_data["quantity"]
        )
        db.add(db_assoc)

    db.commit() # Commit associations and product stock updates
    db.refresh(new_transaction) # Refresh to load the 'products' relationship
    return new_transaction


@router.post("/sell", response_model=schemas.Transaction, status_code=status.HTTP_201_CREATED)
def create_sell_transaction(
    transaction_data: schemas.TransactionCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    product_associations_data, total_price, total_products = _process_transaction_products(
        db, transaction_data.products_involved, schemas.TransactionType.SELL
    )

    new_transaction = models.Transaction(
        totalProducts=total_products,
        totalPrice=total_price,
        transactionType=schemas.TransactionType.SELL,
        transactionStatus=transaction_data.transactionStatus or schemas.TransactionStatus.COMPLETED, # Sell usually completed
        description=transaction_data.description,
        note=transaction_data.note,
        user_id=current_user.id,
        supplier_id=transaction_data.supplier_id # Supplier might be null for sell
    )
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)

    for assoc_data in product_associations_data:
        db_assoc = models.TransactionProductAssociation(
            transaction_id=new_transaction.id,
            product_id=assoc_data["product_id"],
            quantity=assoc_data["quantity"]
        )
        db.add(db_assoc)

    db.commit()
    db.refresh(new_transaction)
    return new_transaction


@router.get("/all", response_model=List[schemas.Transaction])
def read_transactions(
    searchText: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db)
):
    query = db.query(models.Transaction)

    if searchText:
        search_term = f"%{searchText.lower()}%"
        query = query.join(models.User).outerjoin(models.Supplier).filter(
            models.Transaction.id.cast(str).ilike(search_term) |
            models.Transaction.description.ilike(search_term) |
            models.Transaction.note.ilike(search_term) |
            models.User.name.ilike(search_term) |
            models.User.email.ilike(search_term) |
            models.Supplier.name.ilike(search_term)
            # Could also join products and search product names, but that's more complex for a simple search
        )

    transactions = query.order_by(models.Transaction.createdAt.desc()).offset(skip).limit(limit).all()
    return transactions

@router.get("/{id}", response_model=schemas.Transaction)
def read_transaction(id: int, db: Session = Depends(database.get_db)):
    db_transaction = db.query(models.Transaction).filter(models.Transaction.id == id).first()
    if db_transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return db_transaction

@router.put("/update/{id}", response_model=schemas.Transaction)
def update_transaction_status_endpoint( # Renamed to avoid conflict with schema name
    id: int,
    status_update: schemas.TransactionStatusUpdate, # This expects a single 'status' field
    db: Session = Depends(database.get_db)
):
    db_transaction = db.query(models.Transaction).filter(models.Transaction.id == id).first()
    if db_transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # Frontend sends JSON.stringify(status), so status_update.status will be the string value of the enum
    # The Pydantic schema TransactionStatusUpdate already has 'status: TransactionStatus'
    # So FastAPI should handle the conversion from string to the enum member.

    # TODO: Consider implications of changing status, e.g., rolling back stock changes if cancelled.
    # This is complex and depends on business rules. For now, just update status.
    if db_transaction.transactionStatus == schemas.TransactionStatus.COMPLETED and \
       status_update.status == schemas.TransactionStatus.CANCELLED:
        # Basic example: if cancelling a completed transaction, revert stock quantities
        # This is a simplified example; real-world scenarios might be more complex
        # (e.g., what if products were from multiple batches, or prices changed?)
        for assoc in db_transaction.products:
            db_product = db.query(models.Product).filter(models.Product.id == assoc.product_id).first()
            if db_product:
                if db_transaction.transactionType == schemas.TransactionType.SELL:
                    db_product.stockQuantity += assoc.quantity # Add back stock
                elif db_transaction.transactionType == schemas.TransactionType.PURCHASE:
                    db_product.stockQuantity -= assoc.quantity # Remove stock
                db.add(db_product)


    db_transaction.transactionStatus = status_update.status
    db_transaction.updatedAt = datetime.utcnow() # Manually set updatedAt if not auto by DB
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

@router.get("/by-month-year", response_model=List[schemas.Transaction])
def read_transactions_by_month_year(
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2000, le=datetime.now().year + 5),
    db: Session = Depends(database.get_db)
):
    transactions = db.query(models.Transaction).filter(
        and_(
            extract('month', models.Transaction.createdAt) == month,
            extract('year', models.Transaction.createdAt) == year
        )
    ).order_by(models.Transaction.createdAt.desc()).all()
    return transactions
