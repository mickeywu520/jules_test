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
