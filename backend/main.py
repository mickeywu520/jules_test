from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
import logging
import traceback
import os

from .database import engine, create_db_and_tables #, SessionLocal, Base (not directly used here but good for context)
from .routers import auth, users, categories, suppliers, products, transactions, customers, purchase_orders, goods_receipts, sales_orders, customer_types
from .error_messages import get_friendly_message, detect_error_type
# from . import models # models are used by create_db_and_tables via database.py

# Call this function to create DB tables when the application starts
# This is useful for development, might be handled by migrations (e.g. Alembic) in production
# models.Base.metadata.create_all(bind=engine) # Alternative way to call it if models is imported directly
# Using the function from database.py is cleaner
# create_db_and_tables() # This will be called via startup event

app = FastAPI(title="Inventory Management API", version="1.0.0")

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 全域異常處理器
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """處理 HTTP 異常，返回友善的錯誤訊息"""
    error_type = detect_error_type(exc.detail)
    friendly_message = get_friendly_message(error_type, exc.detail)

    logger.warning(f"HTTP Exception: {exc.status_code} - {exc.detail}")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "message": friendly_message,
            "code": error_type
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """處理請求驗證錯誤"""
    logger.warning(f"Validation Error: {exc.errors()}")

    # 提取第一個錯誤的詳細資訊
    first_error = exc.errors()[0] if exc.errors() else {}
    field_name = " -> ".join(str(loc) for loc in first_error.get("loc", []))
    error_msg = first_error.get("msg", "資料格式錯誤")

    friendly_message = f"欄位 '{field_name}' {error_msg}" if field_name else "資料格式錯誤，請檢查輸入內容"

    return JSONResponse(
        status_code=422,
        content={
            "message": friendly_message,
            "code": "VALIDATION_ERROR"
        }
    )

@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """處理資料庫相關錯誤"""
    logger.error(f"Database Error: {str(exc)}")

    error_detail = str(exc)
    if "duplicate key" in error_detail.lower() or "unique constraint" in error_detail.lower():
        friendly_message = "資料重複，請檢查是否已存在相同的記錄"
        error_code = "CONSTRAINT_VIOLATION"
    elif "foreign key" in error_detail.lower():
        friendly_message = "資料關聯錯誤，請檢查相關資料是否存在"
        error_code = "CONSTRAINT_VIOLATION"
    else:
        friendly_message = get_friendly_message("DATABASE_ERROR")
        error_code = "DATABASE_ERROR"

    return JSONResponse(
        status_code=500,
        content={
            "message": friendly_message,
            "code": error_code
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """處理所有其他未捕獲的異常"""
    logger.error(f"Unhandled Exception: {type(exc).__name__}: {str(exc)}")
    logger.error(f"Traceback: {traceback.format_exc()}")

    return JSONResponse(
        status_code=500,
        content={
            "message": get_friendly_message("INTERNAL_SERVER_ERROR"),
            "code": "INTERNAL_SERVER_ERROR"
        }
    )

# CORS Middleware Configuration
# 使用 PRODUCTION flag 來控制 CORS 設定
# 在 Hugging Face Spaces 中設定 PRODUCTION=true 來跳過 CORS 配置
PRODUCTION = os.getenv("PRODUCTION", "false").lower() == "true"

if not PRODUCTION:
    # 非生產環境（開發/測試）：配置 CORS 以支持本地和手機測試
    print("🔧 Development mode: Configuring CORS for local testing...")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 開發環境允許所有來源以支持手機測試
        allow_credentials=True,
        allow_methods=["*"], # Allows all methods (GET, POST, etc.)
        allow_headers=["*"], # Allows all headers
    )
    print("✅ CORS configured for development environment")
else:
    # 生產環境：跳過 CORS 配置，讓 Hugging Face Spaces 處理
    print("🚀 Production mode: Skipping CORS configuration (handled by deployment platform)")
    print("✅ CORS configuration skipped for production environment")

# 請求記錄中介軟體
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """記錄所有請求和回應"""
    import time
    start_time = time.time()

    # 記錄請求
    logger.info(f"Request: {request.method} {request.url}")

    try:
        response = await call_next(request)
        process_time = time.time() - start_time

        # 記錄成功回應
        logger.info(f"Response: {request.method} {request.url} - {response.status_code} - {process_time:.2f}s")

        return response
    except Exception as e:
        process_time = time.time() - start_time

        # 記錄錯誤
        logger.error(f"Error: {request.method} {request.url} - {type(e).__name__}: {str(e)} - {process_time:.2f}s")

        # 重新拋出異常，讓全域異常處理器處理
        raise

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
import os
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")


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
app.include_router(goods_receipts.router)
app.include_router(sales_orders.router)
app.include_router(customer_types.router)


# Root endpoint (optional, good for a health check or API info)
@app.get("/", tags=["Root"])
async def read_root():
    return {
        "message": "Welcome to the Inventory Management API!",
        "documentation": "/docs",
        "redoc": "/redoc"
    }

# 健康檢查端點
@app.get("/health", tags=["Health"])
async def health_check():
    """檢查服務健康狀態"""
    from .database import SessionLocal
    from sqlalchemy.sql import text

    try:
        # 檢查資料庫連接
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()

        return {
            "status": "healthy",
            "database": "connected",
            "message": "服務運行正常"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="Service unhealthy"
        )

# How to run this application (from the project root, where 'backend' folder is):
# uvicorn backend.main:app --reload --port 5050
# Ensure PostgreSQL is running and the 'inventory_db_fastapi' database is created.
