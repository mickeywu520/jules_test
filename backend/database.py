from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Replace with your actual PostgreSQL connection string
# Format: postgresql://user:password@host:port/database_name
DATABASE_URL = "postgresql://postgres:123456@localhost:5432/inventory_db_fastapi"
# It's good practice to use environment variables for credentials in a real app.

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Function to create all tables
def create_db_and_tables():
    # Import all models here before calling create_all
    # This ensures they are registered with Base.metadata
    from . import models # This ensures they are registered with Base.metadata
    Base.metadata.create_all(bind=engine)
    print("Database tables created (if they didn't exist).")
