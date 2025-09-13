from typing import List, Dict
import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

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
        bankAccount=customer.bankAccount,
        notes=customer.notes,
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
    
    # 為每個客戶添加欄位修改資訊
    for customer in customers:
        # 獲取最近30天的審計日誌
        from datetime import datetime, timedelta
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        audit_logs = db.query(models.CustomerAuditLog).filter(
            models.CustomerAuditLog.customer_id == customer.id,
            models.CustomerAuditLog.changed_at >= thirty_days_ago
        ).all()
        
        # 建立欄位修改映射
        modified_fields = set()
        for log in audit_logs:
            modified_fields.add(log.field_name)
        
        # 將修改過的欄位資訊附加到客戶物件
        customer.modified_fields = list(modified_fields)
        
        # 調試日誌
        if modified_fields:
            print(f"Customer {customer.id} has modified fields: {list(modified_fields)}")
    
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
def update_customer(
    id: int, 
    customer_update: schemas.CustomerUpdate, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
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

    # 記錄審計日誌 - 在更新前記錄舊值
    update_data = customer_update.model_dump(exclude_unset=True)
    for field, new_value in update_data.items():
        old_value = getattr(db_customer, field, None)
        
        # 只有當值真的改變時才記錄
        if str(old_value) != str(new_value):
            audit_log = models.CustomerAuditLog(
                customer_id=id,
                field_name=field,
                old_value=str(old_value) if old_value is not None else None,
                new_value=str(new_value) if new_value is not None else None,
                changed_by=current_user.id,
                action_type="UPDATE"
            )
            db.add(audit_log)

    # Update fields if provided
    for field, value in update_data.items():
        setattr(db_customer, field, value)

    db.commit()
    db.refresh(db_customer)
    return db_customer

@router.get("/{customer_id}/business-hours", response_model=schemas.CustomerBusinessHoursResponse)
def get_customer_business_hours(customer_id: int, db: Session = Depends(database.get_db)):
    customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    weekly: List[schemas.WeeklyDay] = []
    # 預設 0..6 每日都回傳（即使沒有資料也有 is_open=false）
    existing = {bh.weekday: bh for bh in db.query(models.CustomerBusinessHour)
                .filter(models.CustomerBusinessHour.customer_id == customer_id)
                .options(joinedload(models.CustomerBusinessHour.intervals)).all()}

    for weekday in range(7):
        if weekday in existing:
            bh = existing[weekday]
            weekly.append(schemas.WeeklyDay(
                weekday=weekday,
                is_open=bh.is_open,
                ranges=[schemas.TimeRange(start=iv.start_time.strftime('%H:%M'), end=iv.end_time.strftime('%H:%M')) for iv in bh.intervals]
            ))
        else:
            weekly.append(schemas.WeeklyDay(weekday=weekday, is_open=False, ranges=[]))

    exceptions_q = db.query(models.CustomerBusinessHourException).filter(
        models.CustomerBusinessHourException.customer_id == customer_id
    ).all()
    exceptions = []
    for ex in exceptions_q:
        ranges = None
        if ex.start_time and ex.end_time:
            ranges = [schemas.TimeRange(start=ex.start_time.strftime('%H:%M'), end=ex.end_time.strftime('%H:%M'))]
        exceptions.append(schemas.BusinessHourException(
            date=ex.date,
            is_open=ex.is_open,
            ranges=ranges,
            reason=ex.reason
        ))

    return schemas.CustomerBusinessHoursResponse(weekly=weekly, exceptions=exceptions or None)

@router.put("/{customer_id}/business-hours", response_model=schemas.CustomerBusinessHoursResponse)
def put_customer_business_hours(customer_id: int, payload: schemas.CustomerBusinessHoursUpdate, db: Session = Depends(database.get_db)):
    customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # 清空舊的 weekly 設定
    db.query(models.CustomerBusinessHourInterval).filter(
        models.CustomerBusinessHourInterval.business_hour_id.in_(
            db.query(models.CustomerBusinessHour.id).filter(models.CustomerBusinessHour.customer_id == customer_id)
        )
    ).delete(synchronize_session=False)
    db.query(models.CustomerBusinessHour).filter(
        models.CustomerBusinessHour.customer_id == customer_id
    ).delete(synchronize_session=False)

    # 建立新的 weekly 設定
    for day in payload.weekly:
        bh = models.CustomerBusinessHour(
            customer_id=customer_id,
            weekday=day.weekday,
            is_open=day.is_open
        )
        db.add(bh)
        db.flush()  # 取 id
        if day.is_open:
            for r in (day.ranges or []):
                iv = models.CustomerBusinessHourInterval(
                    business_hour_id=bh.id,
                    start_time=_parse_time(r.start),
                    end_time=_parse_time(r.end),
                )
                db.add(iv)

    # 清空舊的 exceptions
    db.query(models.CustomerBusinessHourException).filter(
        models.CustomerBusinessHourException.customer_id == customer_id
    ).delete(synchronize_session=False)

    # 新增例外日
    for ex in (payload.exceptions or []):
        start_time = _parse_time(ex.ranges[0].start) if ex.ranges and len(ex.ranges) > 0 else None
        end_time = _parse_time(ex.ranges[0].end) if ex.ranges and len(ex.ranges) > 0 else None
        ex_row = models.CustomerBusinessHourException(
            customer_id=customer_id,
            date=ex.date,
            is_open=ex.is_open,
            start_time=start_time,
            end_time=end_time,
            reason=ex.reason
        )
        db.add(ex_row)

    db.commit()

    return get_customer_business_hours(customer_id, db)

# helpers
from datetime import datetime as _dt

def _parse_time(hhmm: str):
    try:
        t = _dt.strptime(hhmm, '%H:%M').time()
        return t
    except Exception:
        raise HTTPException(status_code=400, detail=f"Invalid time format: {hhmm}")

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

# Additional endpoint to search customers by customer type
@router.get("/search-by-type/{customer_type_id}", response_model=List[schemas.Customer])
def search_customers_by_type(customer_type_id: int, db: Session = Depends(database.get_db)):
    customers = db.query(models.Customer).filter(
        models.Customer.customer_type_id == customer_type_id
    ).all()
    return customers

# Additional endpoint to search customers by county
@router.get("/search-by-county/{county}", response_model=List[schemas.Customer])
def search_customers_by_county(county: str, db: Session = Depends(database.get_db)):
    customers = db.query(models.Customer).filter(
        models.Customer.deliveryAddress.contains(county)
    ).all()
    return customers

# Additional endpoint to search customers by district
@router.get("/search-by-district/{district}", response_model=List[schemas.Customer])
def search_customers_by_district(district: str, db: Session = Depends(database.get_db)):
    customers = db.query(models.Customer).filter(
        models.Customer.deliveryAddress.contains(district)
    ).all()
    return customers

# Additional endpoint to search customers by customer code
@router.get("/search-by-code/{customer_code}", response_model=List[schemas.Customer])
def search_customers_by_code(customer_code: str, db: Session = Depends(database.get_db)):
    customers = db.query(models.Customer).filter(
        models.Customer.customerCode.ilike(f"%{customer_code}%")
    ).all()
    return customers

# Additional endpoint to search customers by contact person
@router.get("/search-by-contact-person/{contact_person}", response_model=List[schemas.Customer])
def search_customers_by_contact_person(contact_person: str, db: Session = Depends(database.get_db)):
    customers = db.query(models.Customer).filter(
        models.Customer.contactPerson.ilike(f"%{contact_person}%")
    ).all()
    return customers

# Additional endpoint to search customers by phone number
@router.get("/search-by-phone-number/{phone_number}", response_model=List[schemas.Customer])
def search_customers_by_phone_number(phone_number: str, db: Session = Depends(database.get_db)):
    customers = db.query(models.Customer).filter(
        models.Customer.phoneNumber.ilike(f"%{phone_number}%")
    ).all()
    return customers

# Batch update customers
@router.put("/batch-update", response_model=List[schemas.Customer])
def batch_update_customers(
    customer_ids: List[int], 
    customer_update: schemas.CustomerUpdate, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    # Check if the current user has admin privileges
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理員可以執行批次更新操作"
        )
    
    # Update customers
    updated_customers = []
    business_hours_updates = []  # Store business hours updates for later processing
    
    for customer_id in customer_ids:
        db_customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
        if db_customer:
            # Update fields if provided
            update_data = customer_update.model_dump(exclude_unset=True)
            
            # Handle business hours specially
            if 'businessHours' in update_data:
                business_hours_json = update_data['businessHours']
                # Store for later processing
                business_hours_updates.append((customer_id, business_hours_json))
            
            # Update other fields
            for field, value in update_data.items():
                setattr(db_customer, field, value)
            updated_customers.append(db_customer)
    
    # Commit customer updates first
    db.commit()
    
    # Process business hours updates
    for customer_id, business_hours_json in business_hours_updates:
        try:
            # Parse the JSON string
            business_hours_data = json.loads(business_hours_json)
            print(f"Updating business hours for customer {customer_id} with data: {business_hours_data}")
            
            # Update business hours using the same logic as the dedicated endpoint
            _update_customer_business_hours(customer_id, business_hours_data, db)
            print(f"Successfully updated business hours for customer {customer_id}")
            
        except (json.JSONDecodeError, Exception) as e:
            print(f"Failed to update business hours for customer {customer_id}: {e}")
            # Continue with other customers even if one fails
    
    # Final commit for business hours updates
    db.commit()
    
    # Refresh all updated customers
    for customer in updated_customers:
        db.refresh(customer)
    
    return updated_customers

# Helper function to update customer business hours
def _update_customer_business_hours(customer_id: int, business_hours_data: dict, db: Session):
    """
    Helper function to update customer business hours from parsed JSON data
    """
    customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if not customer:
        return
    
    # Clear existing business hours (same logic as the dedicated endpoint)
    db.query(models.CustomerBusinessHourInterval).filter(
        models.CustomerBusinessHourInterval.business_hour_id.in_(
            db.query(models.CustomerBusinessHour.id).filter(models.CustomerBusinessHour.customer_id == customer_id)
        )
    ).delete(synchronize_session=False)
    db.query(models.CustomerBusinessHour).filter(
        models.CustomerBusinessHour.customer_id == customer_id
    ).delete(synchronize_session=False)
    
    # Add weekly business hours
    weekly_data = business_hours_data.get('weekly', [])
    for day_data in weekly_data:
        weekday = day_data.get('weekday', 0)
        is_open = day_data.get('is_open', False)
        
        # Create business hour record
        business_hour = models.CustomerBusinessHour(
            customer_id=customer_id,
            weekday=weekday,
            is_open=is_open
        )
        db.add(business_hour)
        db.flush()  # Get the ID
        
        # Add time intervals if open
        if is_open:
            ranges = day_data.get('ranges', [])
            for range_data in ranges:
                interval = models.CustomerBusinessHourInterval(
                    business_hour_id=business_hour.id,  # Correct field name
                    start_time=_parse_time(range_data.get('start', '09:00')),
                    end_time=_parse_time(range_data.get('end', '18:00'))
                )
                db.add(interval)
    
    # Clear existing exceptions
    db.query(models.CustomerBusinessHourException).filter(
        models.CustomerBusinessHourException.customer_id == customer_id
    ).delete(synchronize_session=False)
    
    # Add exceptions
    exceptions_data = business_hours_data.get('exceptions', [])
    for exception_data in exceptions_data:
        ranges = exception_data.get('ranges', [])
        start_time = _parse_time(ranges[0].get('start')) if ranges and len(ranges) > 0 else None
        end_time = _parse_time(ranges[0].get('end')) if ranges and len(ranges) > 0 else None
        
        exception = models.CustomerBusinessHourException(
            customer_id=customer_id,
            date=exception_data.get('date'),
            is_open=exception_data.get('is_open', False),
            start_time=start_time,
            end_time=end_time,
            reason=exception_data.get('reason')
        )
        db.add(exception)

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
    # 使用包含匹配而非精確匹配，解決編碼問題
    customer_type_name = customer_type.type_name
    if "月結店家" in customer_type_name:
        prefix = "B"
    elif "下收店家" in customer_type_name:
        prefix = "D"
    elif "連鎖體系" in customer_type_name or "連鎖" in customer_type_name:
        prefix = "AA"
    elif "零售" in customer_type_name:
        prefix = "X"
    else:
        prefix = "CUS"  # 默認前綴
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

# 獲取客戶審計日誌
@router.get("/{customer_id}/audit-logs")
def get_customer_audit_logs(customer_id: int, db: Session = Depends(database.get_db)):
    """獲取客戶的修改歷史記錄"""
    customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # 獲取最近的審計日誌（最近30天）
    from datetime import datetime, timedelta
    thirty_days_ago = datetime.now() - timedelta(days=30)
    
    audit_logs = db.query(models.CustomerAuditLog).filter(
        models.CustomerAuditLog.customer_id == customer_id,
        models.CustomerAuditLog.changed_at >= thirty_days_ago
    ).order_by(models.CustomerAuditLog.changed_at.desc()).all()
    
    # 格式化返回數據
    formatted_logs = []
    for log in audit_logs:
        formatted_logs.append({
            "id": log.id,
            "field_name": log.field_name,
            "old_value": log.old_value,
            "new_value": log.new_value,
            "changed_at": log.changed_at.isoformat(),
            "changed_by": log.changed_by,
            "action_type": log.action_type
        })
    
    return {"audit_logs": formatted_logs}

# 獲取特定欄位的最後修改記錄
@router.get("/{customer_id}/field-history/{field_name}")
def get_field_history(customer_id: int, field_name: str, db: Session = Depends(database.get_db)):
    """獲取特定欄位的最後修改記錄"""
    # 獲取該欄位的最新修改記錄
    latest_change = db.query(models.CustomerAuditLog).filter(
        models.CustomerAuditLog.customer_id == customer_id,
        models.CustomerAuditLog.field_name == field_name
    ).order_by(models.CustomerAuditLog.changed_at.desc()).first()
    
    if not latest_change:
        return {"has_history": False}
    
    return {
        "has_history": True,
        "field_name": latest_change.field_name,
        "old_value": latest_change.old_value,
        "new_value": latest_change.new_value,
        "changed_at": latest_change.changed_at.isoformat(),
        "changed_by": latest_change.changed_by
    }
