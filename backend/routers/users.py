from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import database, models, schemas, security # Adjusted imports

router = APIRouter(
    prefix="/api/users", # This prefix will be used by main.py
    tags=["Users"],
)

@router.get("/current", response_model=schemas.User)
async def read_users_me(current_user: models.User = Depends(security.get_current_active_user)):
    # current_user is already a SQLAlchemy model instance from get_current_active_user
    return current_user

# Potential endpoint for updating user profile (as per schemas.UserUpdate)
@router.put("/current", response_model=schemas.User)
async def update_user_me(
    user_update: schemas.UserUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    user_data = user_update.dict(exclude_unset=True) # Get only provided fields

    for key, value in user_data.items():
        setattr(current_user, key, value)

    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user

@router.get("/all", response_model=List[schemas.User])
async def get_all_users(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_admin_user)
):
    """獲取所有用戶列表 - 僅ADMIN可訪問"""
    users = db.query(models.User).all()
    return users

@router.put("/{user_id}", response_model=schemas.User)
async def update_user(
    user_id: int,
    user_update: schemas.UserUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_admin_user)
):
    """更新用戶資訊 - 僅ADMIN可訪問"""
    # 查找要更新的用戶
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用戶不存在")

    # 防止將用戶角色設置為ADMIN
    if user_update.role == models.UserRole.ADMIN:
        raise HTTPException(status_code=400, detail="不能將用戶角色設置為ADMIN")

    # 檢查郵箱是否已被其他用戶使用
    if user_update.email and user_update.email != user.email:
        existing_user = db.query(models.User).filter(
            models.User.email == user_update.email,
            models.User.id != user_id
        ).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="郵箱已被其他用戶使用")

    # 更新用戶資訊
    if user_update.name is not None:
        user.name = user_update.name
    if user_update.email is not None:
        user.email = user_update.email
    if user_update.phoneNumber is not None:
        user.phoneNumber = user_update.phoneNumber
    if user_update.role is not None:
        user.role = user_update.role

    db.commit()
    db.refresh(user)
    return user
