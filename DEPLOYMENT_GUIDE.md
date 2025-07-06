# 部署指南 - Deployment Guide

## 🚀 Hugging Face Spaces 部署

### 環境變量配置

在 Hugging Face Spaces 的 Settings 中添加以下環境變量：

```
PRODUCTION=true
DB_HOST=<HF提供的主機名>
DB_PORT=6543
DB_NAME=<HF提供的資料庫名>
DB_USER=<HF提供的用戶名>
DB_PASSWORD=<HF提供的密碼>
```

### 為什麼需要這個設定？

- **開發環境** (`PRODUCTION=false` 或未設定)：
  - 啟用 CORS 配置，允許所有來源 (`allow_origins=["*"]`)
  - 使用本地資料庫配置 (`DATABASE_URL` 從 .env 文件)
  - 支持本地開發和手機測試
  - 允許跨域請求

- **生產環境** (`PRODUCTION=true`)：
  - 跳過 CORS 配置
  - 使用 HF Spaces 注入的資料庫環境變數
  - 讓 Hugging Face Spaces 等部署平台處理跨域問題
  - 避免安全風險和配置衝突

### 部署步驟

1. **準備代碼**：確保所有代碼已提交
2. **設定環境變量**：在 HF Spaces Settings 中添加 `PRODUCTION=true`
3. **部署**：推送到 Hugging Face Spaces
4. **驗證**：檢查日誌中是否顯示 "Production mode: Skipping CORS configuration"

## 🔧 本地開發

### 環境變量配置

創建 `backend/.env` 文件：

```
PRODUCTION=false
```

或者不設定（默認為開發模式）

### 手機測試

當 `PRODUCTION=false` 時，後端會自動配置 CORS 以支持：
- 本地訪問 (`localhost:4200`)
- 局域網訪問 (`192.168.x.x:4200`)
- 手機訪問

## 📋 日誌輸出

### 開發模式
```
🔧 Development mode: Using local database configuration...
✅ Development database URL configured: postgresql://postgres:***@localhost:5432/inventory_db_fastapi
🔧 Development mode: Configuring CORS for local testing...
✅ CORS configured for development environment
```

### 生產模式
```
🚀 Production mode: Using Hugging Face Space database configuration...
✅ Production database URL configured: postgresql+psycopg://user:***@host:6543/dbname
🚀 Production mode: Skipping CORS configuration (handled by deployment platform)
✅ CORS configuration skipped for production environment
```

## ⚠️ 注意事項

1. **安全性**：生產環境不要設定 `PRODUCTION=false`
2. **測試**：部署前先在本地測試 `PRODUCTION=true` 模式
3. **日誌**：檢查啟動日誌確認 CORS 配置狀態
