from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text # For db.execute(text("SELECT 1"))
import os
import psycopg

# 從環境變數獲取資料庫連線資訊
# Hugging Face Space 會在運行時自動注入這些變數
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT") # 現在是 '6543'
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# SQLAlchemy 初始化
DATABASE_URL = f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

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
    print("Attempting to create database tables...")
    # Ensure engine is defined in the scope; it should be global in database.py
    print(f"  Database URL: {engine.url}")

    # Ensure Base is populated by importing models
    # This import is critical for Base.metadata to know about the tables.
    try:
        from . import models
        print(f"  Successfully imported 'backend.models'.")
    except ImportError as e:
        print(f"  CRITICAL ERROR: Could not import 'backend.models': {e}")
        print(f"  SQLAlchemy Base metadata will be empty. Aborting table creation.")
        return

    print(f"  SQLAlchemy Base metadata has tables: {list(Base.metadata.tables.keys())}")

    if not list(Base.metadata.tables.keys()):
        print("  WARNING: No tables found in Base.metadata even after import attempt.")
        print("           Check models.py for correct model definitions inheriting from Base,")
        print("           and ensure no circular dependencies prevent their registration.")
        return

    try:
        print("  Executing Base.metadata.create_all(bind=engine)...")
        Base.metadata.create_all(bind=engine)
        print("  Base.metadata.create_all(bind=engine) executed successfully.")
    except Exception as e:
        print(f"  CRITICAL ERROR during Base.metadata.create_all: {e}")
        print(f"  This usually means a problem connecting to the database (wrong URL, server down, DB not created externally),")
        print(f"  network issues, or permissions issues for the database user.")
        # import traceback # Uncomment for full traceback if needed in deeper debugging
        # traceback.print_exc()
        return # Stop if table creation failed

    print("  Diagnostic check: Verifying database connection and table presence...")
    db = None
    try:
        db = SessionLocal() # SessionLocal should be defined globally in database.py

        # Verify connection by executing a simple query
        db.execute(text("SELECT 1"))
        print("  Successfully executed a simple query (SELECT 1). Database connection is OK.")

        # Check if 'users' table (as an example) exists and can be queried
        if 'users' in Base.metadata.tables.keys():
            user_count = db.query(models.User).count() # Assumes models.User is accessible
            print(f"  Successfully queried 'users' table. Number of users found: {user_count}.")
            print("  This indicates the 'users' table was created and is queryable.")
        else:
            print("  WARNING: 'users' table key not found in Base.metadata after create_all.")
            print("           This is unexpected if models were registered correctly.")

        print("  Diagnostic database check complete.")

    except Exception as e:
        print(f"  ERROR during diagnostic database check (after create_all): {e}")
        print(f"  This could mean tables were not actually created, or there's a post-creation query issue.")
        # import traceback
        # traceback.print_exc()
    finally:
        if db:
            db.close()

    print("Finished create_db_and_tables function.")
