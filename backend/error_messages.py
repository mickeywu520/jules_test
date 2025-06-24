"""
統一錯誤訊息管理
將技術性錯誤訊息轉換為用戶友善的中文訊息
"""

# 錯誤訊息對照表
ERROR_MESSAGES = {
    # 類別相關錯誤
    "CATEGORY_NAME_EXISTS": "類別名稱已存在",
    "CATEGORY_NOT_FOUND": "找不到指定的類別",
    "CATEGORY_HAS_PRODUCTS": "此類別下還有商品，無法刪除",
    
    # 產品相關錯誤
    "PRODUCT_CODE_EXISTS": "商品編號已存在",
    "PRODUCT_NOT_FOUND": "找不到指定的商品",
    "PRODUCT_HAS_TRANSACTIONS": "此商品有相關交易記錄，無法刪除",
    
    # 客戶相關錯誤
    "CUSTOMER_CODE_EXISTS": "客戶編號已存在",
    "CUSTOMER_NOT_FOUND": "找不到指定的客戶",
    "CUSTOMER_HAS_ORDERS": "此客戶有相關訂單，無法刪除",
    
    # 供應商相關錯誤
    "SUPPLIER_NAME_EXISTS": "供應商名稱已存在",
    "SUPPLIER_NOT_FOUND": "找不到指定的供應商",
    "SUPPLIER_HAS_ORDERS": "此供應商有相關訂單，無法刪除",
    
    # 用戶相關錯誤
    "EMAIL_ALREADY_REGISTERED": "此電子郵件已被註冊",
    "USER_NOT_FOUND": "找不到指定的用戶",
    "INCORRECT_CREDENTIALS": "電子郵件或密碼錯誤",
    "UNAUTHORIZED": "您沒有權限執行此操作",
    
    # 採購單相關錯誤
    "PURCHASE_ORDER_NOT_FOUND": "找不到指定的採購單",
    "PURCHASE_ORDER_ALREADY_RECEIVED": "此採購單已完成收貨",
    "INVALID_PURCHASE_ORDER_STATUS": "採購單狀態無效",
    
    # 銷售單相關錯誤
    "SALES_ORDER_NOT_FOUND": "找不到指定的銷售單",
    "SALES_ORDER_ALREADY_SHIPPED": "此銷售單已出貨",
    "INVALID_SALES_ORDER_STATUS": "銷售單狀態無效",
    "INSUFFICIENT_STOCK": "庫存不足",
    
    # 入庫單相關錯誤
    "GOODS_RECEIPT_NOT_FOUND": "找不到指定的入庫單",
    "INVALID_GOODS_RECEIPT_STATUS": "入庫單狀態無效",
    
    # 交易相關錯誤
    "TRANSACTION_NOT_FOUND": "找不到指定的交易記錄",
    "INVALID_TRANSACTION_STATUS": "交易狀態無效",
    
    # 資料庫相關錯誤
    "DATABASE_ERROR": "資料庫操作失敗，請稍後再試",
    "CONNECTION_ERROR": "資料庫連線錯誤，請稍後再試",
    "CONSTRAINT_VIOLATION": "資料完整性錯誤，請檢查相關資料",
    
    # 驗證相關錯誤
    "VALIDATION_ERROR": "資料格式錯誤，請檢查輸入內容",
    "REQUIRED_FIELD_MISSING": "必填欄位不能為空",
    "INVALID_FORMAT": "資料格式不正確",
    "INVALID_VALUE": "輸入值無效",
    
    # 系統相關錯誤
    "INTERNAL_SERVER_ERROR": "系統內部錯誤，請稍後再試",
    "SERVICE_UNAVAILABLE": "服務暫時無法使用，請稍後再試",
    "TIMEOUT_ERROR": "請求超時，請稍後再試",
    
    # 檔案相關錯誤
    "FILE_NOT_FOUND": "找不到指定的檔案",
    "FILE_UPLOAD_ERROR": "檔案上傳失敗",
    "INVALID_FILE_FORMAT": "檔案格式不支援",
    "FILE_TOO_LARGE": "檔案大小超過限制",
    
    # 權限相關錯誤
    "ACCESS_DENIED": "存取被拒絕",
    "INSUFFICIENT_PERMISSIONS": "權限不足",
    "TOKEN_EXPIRED": "登入已過期，請重新登入",
    "INVALID_TOKEN": "無效的認證令牌",
}

def get_friendly_message(error_key: str, default_message: str = None) -> str:
    """
    根據錯誤代碼獲取友善的錯誤訊息
    
    Args:
        error_key: 錯誤代碼
        default_message: 如果找不到對應訊息時的預設訊息
    
    Returns:
        友善的錯誤訊息
    """
    return ERROR_MESSAGES.get(error_key, default_message or "系統發生未知錯誤")

def detect_error_type(detail_message: str) -> str:
    """
    根據詳細錯誤訊息自動檢測錯誤類型
    
    Args:
        detail_message: 原始錯誤訊息
    
    Returns:
        對應的錯誤代碼
    """
    detail_lower = detail_message.lower()
    
    # 類別相關
    if "category" in detail_lower and "already exists" in detail_lower:
        return "CATEGORY_NAME_EXISTS"
    elif "category not found" in detail_lower:
        return "CATEGORY_NOT_FOUND"
    elif "category" in detail_lower and "associated products" in detail_lower:
        return "CATEGORY_HAS_PRODUCTS"
    
    # 產品相關
    elif "product code already exists" in detail_lower:
        return "PRODUCT_CODE_EXISTS"
    elif "product not found" in detail_lower:
        return "PRODUCT_NOT_FOUND"
    
    # 客戶相關
    elif "customer" in detail_lower and "already exists" in detail_lower:
        return "CUSTOMER_CODE_EXISTS"
    elif "customer not found" in detail_lower:
        return "CUSTOMER_NOT_FOUND"
    
    # 供應商相關
    elif "supplier" in detail_lower and "already exists" in detail_lower:
        return "SUPPLIER_NAME_EXISTS"
    elif "supplier not found" in detail_lower:
        return "SUPPLIER_NOT_FOUND"
    
    # 用戶相關
    elif "email already registered" in detail_lower:
        return "EMAIL_ALREADY_REGISTERED"
    elif "incorrect email or password" in detail_lower:
        return "INCORRECT_CREDENTIALS"
    elif "user not found" in detail_lower:
        return "USER_NOT_FOUND"
    
    # 採購單相關
    elif "purchase order not found" in detail_lower:
        return "PURCHASE_ORDER_NOT_FOUND"
    
    # 銷售單相關
    elif "sales order not found" in detail_lower:
        return "SALES_ORDER_NOT_FOUND"
    elif "insufficient stock" in detail_lower:
        return "INSUFFICIENT_STOCK"
    
    # 交易相關
    elif "transaction not found" in detail_lower:
        return "TRANSACTION_NOT_FOUND"
    
    # 資料庫相關
    elif any(keyword in detail_lower for keyword in ["database", "connection", "sqlalchemy"]):
        return "DATABASE_ERROR"
    
    # 驗證相關
    elif any(keyword in detail_lower for keyword in ["validation", "field required", "invalid"]):
        return "VALIDATION_ERROR"
    
    # 預設為內部錯誤
    else:
        return "INTERNAL_SERVER_ERROR"
