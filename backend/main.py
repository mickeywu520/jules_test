from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from .database import engine, create_db_and_tables #, SessionLocal, Base (not directly used here but good for context)
from .routers import auth, users, categories, suppliers, products, transactions, customers, purchase_orders
# from . import models # models are used by create_db_and_tables via database.py

# Call this function to create DB tables when the application starts
# This is useful for development, might be handled by migrations (e.g. Alembic) in production
# models.Base.metadata.create_all(bind=engine) # Alternative way to call it if models is imported directly
# Using the function from database.py is cleaner
# create_db_and_tables() # This will be called via startup event

app = FastAPI(title="Inventory Management API", version="1.0.0")

# CORS Middleware Configuration
# The frontend runs on localhost:4200, backend will run on localhost:5050
origins = [
    "http://localhost",
    "http://localhost:4200", # Default Angular dev port
    # Add any other origins if necessary (e.g., deployed frontend URL)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods (GET, POST, etc.)
    allow_headers=["*"], # Allows all headers
)

# --- Event Handlers ---
@app.on_event("startup")
async def startup_event():
    print("Application startup: Creating database and tables if they don't exist...")
    create_db_and_tables() # Create database tables
    print("Database and tables should now be ready.")
    # You could also seed initial data here if needed for development

@app.on_event("shutdown")
async def shutdown_event():
    print("Application shutdown.")


# --- Static Files ---
# Mount the static directory to serve product images
# The path "/static" means that files in "backend/static" directory will be accessible via "/static/..." URL
# For example, an image at "backend/static/product_images/foo.jpg" will be at "/static/product_images/foo.jpg"
app.mount("/static", StaticFiles(directory="backend/static"), name="static")


# --- API Routers ---
# Include all the API routers. The prefix is already defined in each router.
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(categories.router)
app.include_router(suppliers.router)
app.include_router(products.router)
app.include_router(transactions.router)
app.include_router(customers.router)
app.include_router(purchase_orders.router)


# Root endpoint (optional, good for a health check or API info)
@app.get("/", tags=["Root"])
async def read_root():
    return {
        "message": "Welcome to the Inventory Management API!",
        "documentation": "/docs",
        "redoc": "/redoc"
    }

# How to run this application (from the project root, where 'backend' folder is):
# uvicorn backend.main:app --reload --port 5050
# Ensure PostgreSQL is running and the 'inventory_db_fastapi' database is created.
