# Customer API 文檔

## 概述
Customer API 提供了完整的客戶管理功能，包括新增、查詢、更新和刪除客戶資料。

## 資料模型

### Customer 欄位說明
根據您提供的 Excel 欄位，Customer 模型包含以下欄位：

| 欄位名稱 | 資料庫欄位 | 類型 | 必填 | 說明 |
|---------|-----------|------|------|------|
| 客戶類型 | customerType | Enum | ✓ | INDIVIDUAL/COMPANY/GOVERNMENT/OTHER |
| 建檔日期 | createdDate | DateTime | 自動 | 系統自動設定 |
| 業務員編號 | salesPersonId | String | ✗ | 業務員編號 |
| 業務員名稱 | salesPersonName | String | ✗ | 業務員姓名 |
| 客戶編號 | customerCode | String | ✓ | 唯一識別碼 |
| 客戶名稱 | customerName | String | ✓ | 客戶名稱 |
| 客戶聯絡人 | contactPerson | String | ✗ | 聯絡人姓名 |
| 發票抬頭 | invoiceTitle | String | ✗ | 發票抬頭 |
| 統一編號 | taxId | String | ✗ | 統一編號 |
| 電話號碼 | phoneNumber | String | ✗ | 聯絡電話 |
| 傳真號碼 | faxNumber | String | ✗ | 傳真號碼 |
| 送貨地址 | deliveryAddress | Text | ✗ | 送貨地址 |
| 營業時間/公休日 | businessHours | Text | ✗ | 營業時間說明 |
| 收款方式 | paymentMethod | Enum | ✗ | CASH/CREDIT_CARD/BANK_TRANSFER/CHECK/MONTHLY_PAYMENT/OTHER |
| 收款類別 | paymentCategory | Enum | ✗ | PREPAID/CASH_ON_DELIVERY/CREDIT/MONTHLY_SETTLEMENT/OTHER |
| 銷貨額度 | creditLimit | Float | ✗ | 信用額度，預設 0.0 |

## API 端點

### 1. 新增客戶
- **POST** `/api/customers/add`
- **Request Body**: CustomerCreate schema
- **Response**: Customer schema (201 Created)

### 2. 取得所有客戶
- **GET** `/api/customers/all`
- **Query Parameters**: 
  - `skip`: 跳過筆數 (預設: 0)
  - `limit`: 限制筆數 (預設: 100)
- **Response**: List[Customer] (200 OK)

### 3. 根據 ID 取得客戶
- **GET** `/api/customers/{id}`
- **Path Parameters**: `id` (integer)
- **Response**: Customer schema (200 OK)

### 4. 根據客戶編號取得客戶
- **GET** `/api/customers/code/{customer_code}`
- **Path Parameters**: `customer_code` (string)
- **Response**: Customer schema (200 OK)

### 5. 更新客戶
- **PUT** `/api/customers/update/{id}`
- **Path Parameters**: `id` (integer)
- **Request Body**: CustomerUpdate schema
- **Response**: Customer schema (200 OK)

### 6. 刪除客戶
- **DELETE** `/api/customers/delete/{id}`
- **Path Parameters**: `id` (integer)
- **Response**: Customer schema (200 OK)

### 7. 搜尋客戶
- **GET** `/api/customers/search/{search_term}`
- **Path Parameters**: `search_term` (string)
- **Response**: List[Customer] (200 OK)

## 使用範例

### 新增客戶範例
```json
{
  "customerType": "COMPANY",
  "salesPersonId": "SP001",
  "salesPersonName": "張三",
  "customerCode": "CUST001",
  "customerName": "測試公司有限公司",
  "contactPerson": "李四",
  "invoiceTitle": "測試公司有限公司",
  "taxId": "12345678",
  "phoneNumber": "02-12345678",
  "faxNumber": "02-87654321",
  "deliveryAddress": "台北市信義區信義路五段7號",
  "businessHours": "週一至週五 9:00-18:00",
  "paymentMethod": "MONTHLY_PAYMENT",
  "paymentCategory": "MONTHLY_SETTLEMENT",
  "creditLimit": 100000.0
}
```

### 更新客戶範例
```json
{
  "customerName": "更新後的公司名稱",
  "phoneNumber": "02-99999999",
  "creditLimit": 150000.0
}
```

## 枚舉值說明

### CustomerType (客戶類型)
- `INDIVIDUAL`: 個人客戶
- `COMPANY`: 公司客戶
- `GOVERNMENT`: 政府機關
- `OTHER`: 其他

### PaymentMethod (收款方式)
- `CASH`: 現金
- `CREDIT_CARD`: 信用卡
- `BANK_TRANSFER`: 銀行轉帳
- `CHECK`: 支票
- `MONTHLY_PAYMENT`: 月結
- `OTHER`: 其他

### PaymentCategory (收款類別)
- `PREPAID`: 預付
- `CASH_ON_DELIVERY`: 貨到付款
- `CREDIT`: 賒帳
- `MONTHLY_SETTLEMENT`: 月結
- `OTHER`: 其他

## 錯誤處理
- **400 Bad Request**: 客戶編號重複或資料驗證失敗
- **404 Not Found**: 客戶不存在
- **401 Unauthorized**: 未授權存取（需要登入）

## 注意事項
1. 所有 API 端點都需要身份驗證
2. 客戶編號 (customerCode) 必須唯一
3. 建檔日期會自動設定為當前時間
4. 更新時間會在每次更新時自動更新
