from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm # For form data login
from sqlalchemy.orm import Session

from .. import database, models, schemas, security # Adjusted imports

router = APIRouter(
    prefix="/api/auth", # This prefix will be used by main.py
    tags=["Authentication"],
)

@router.post("/register", response_model=schemas.User)
def register_user(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = security.get_password_hash(user.password)
    # Create user instance, ensuring all required fields are present
    # Pydantic model user.dict() might not include fields with default values if not provided by client
    # Correction: models.User has 'password' field for storing the hashed password.
    db_user = models.User(
        email=user.email,
        password=hashed_password, # Storing hashed password in 'password' field of User model
        name=user.name,
        phoneNumber=user.phoneNumber,
        role=user.role
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/login", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first() # form_data.username is used for email
    if not user or not security.verify_password(form_data.password, user.password): # user.password holds the hash
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = security.create_access_token(
        data={"sub": user.email} # "sub" is standard for subject (user identifier)
    )
    return {"access_token": access_token, "token_type": "bearer"}
