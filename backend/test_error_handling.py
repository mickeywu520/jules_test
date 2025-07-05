"""
測試統一錯誤處理系統
"""
import requests
import json

# API 基礎 URL
BASE_URL = "http://localhost:8000/api"

def test_error_handling():
    """測試錯誤處理系統"""
    print("=" * 80)
    print("統一錯誤處理系統測試")
    print("=" * 80)
    
    try:
        # 1. 測試健康檢查
        print("\n1. 測試健康檢查:")
        response = requests.get(f"{BASE_URL.replace('/api', '')}/health")
        print(f"   狀態碼: {response.status_code}")
        if response.status_code == 200:
            health_data = response.json()
            print(f"   服務狀態: {health_data.get('status', 'N/A')}")
            print(f"   資料庫: {health_data.get('database', 'N/A')}")
            print(f"   訊息: {health_data.get('message', 'N/A')}")
        else:
            print(f"   錯誤: {response.text}")
        
        # 2. 測試重複類別名稱錯誤
        print("\n2. 測試重複類別名稱錯誤:")
        category_data = {"name": "測試類別"}
        
        # 先創建一個類別
        response = requests.post(f"{BASE_URL}/categories/add", json=category_data)
        print(f"   第一次創建 - 狀態碼: {response.status_code}")
        
        # 再次創建相同名稱的類別（應該失敗）
        response = requests.post(f"{BASE_URL}/categories/add", json=category_data)
        print(f"   第二次創建 - 狀態碼: {response.status_code}")
        if response.status_code != 200:
            error_data = response.json()
            print(f"   錯誤訊息: {error_data.get('message', 'N/A')}")
            print(f"   錯誤代碼: {error_data.get('code', 'N/A')}")
            print(f"   完整回應: {json.dumps(error_data, ensure_ascii=False, indent=2)}")
        
        # 3. 測試重複產品編號錯誤
        print("\n3. 測試重複產品編號錯誤:")
        
        # 先獲取類別列表
        categories_response = requests.get(f"{BASE_URL}/categories/all")
        if categories_response.status_code == 200:
            categories = categories_response.json()
            if categories:
                category_id = categories[0]['id']
                
                product_data = {
                    "productCode": "TEST001",
                    "productName": "測試產品",
                    "unit": "個",
                    "category_id": category_id
                }
                
                # 先創建一個產品
                response = requests.post(f"{BASE_URL}/products/add", json=product_data)
                print(f"   第一次創建產品 - 狀態碼: {response.status_code}")
                
                # 再次創建相同編號的產品（應該失敗）
                response = requests.post(f"{BASE_URL}/products/add", json=product_data)
                print(f"   第二次創建產品 - 狀態碼: {response.status_code}")
                if response.status_code != 200:
                    error_data = response.json()
                    print(f"   錯誤訊息: {error_data.get('message', 'N/A')}")
                    print(f"   錯誤代碼: {error_data.get('code', 'N/A')}")
                    print(f"   完整回應: {json.dumps(error_data, ensure_ascii=False, indent=2)}")
            else:
                print("   沒有可用的類別，跳過產品測試")
        else:
            print("   無法獲取類別列表，跳過產品測試")
        
        # 4. 測試重複註冊錯誤
        print("\n4. 測試重複註冊錯誤:")
        user_data = {
            "email": "test@example.com",
            "name": "測試用戶",
            "phoneNumber": "0912345678",
            "password": "password123"
        }
        
        # 先註冊一個用戶
        response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
        print(f"   第一次註冊 - 狀態碼: {response.status_code}")
        
        # 再次註冊相同郵箱（應該失敗）
        response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
        print(f"   第二次註冊 - 狀態碼: {response.status_code}")
        if response.status_code != 200:
            error_data = response.json()
            print(f"   錯誤訊息: {error_data.get('message', 'N/A')}")
            print(f"   錯誤代碼: {error_data.get('code', 'N/A')}")
            print(f"   完整回應: {json.dumps(error_data, ensure_ascii=False, indent=2)}")
        
        # 5. 測試驗證錯誤
        print("\n5. 測試驗證錯誤:")
        invalid_data = {
            "name": "",  # 空名稱
            "email": "invalid-email"  # 無效郵箱格式
        }
        
        response = requests.post(f"{BASE_URL}/categories/add", json=invalid_data)
        print(f"   無效資料請求 - 狀態碼: {response.status_code}")
        if response.status_code != 200:
            error_data = response.json()
            print(f"   錯誤訊息: {error_data.get('message', 'N/A')}")
            print(f"   錯誤代碼: {error_data.get('code', 'N/A')}")
            print(f"   完整回應: {json.dumps(error_data, ensure_ascii=False, indent=2)}")
        
        # 6. 測試找不到資源錯誤
        print("\n6. 測試找不到資源錯誤:")
        response = requests.get(f"{BASE_URL}/categories/99999")  # 不存在的 ID
        print(f"   查詢不存在的類別 - 狀態碼: {response.status_code}")
        if response.status_code != 200:
            error_data = response.json()
            print(f"   錯誤訊息: {error_data.get('message', 'N/A')}")
            print(f"   錯誤代碼: {error_data.get('code', 'N/A')}")
            print(f"   完整回應: {json.dumps(error_data, ensure_ascii=False, indent=2)}")
        
        print("\n" + "=" * 80)
        print("錯誤處理測試完成")
        print("=" * 80)
        
    except requests.exceptions.ConnectionError:
        print("❌ 無法連接到後端服務，請確認後端是否正在運行")
    except Exception as e:
        print(f"❌ 測試時發生錯誤: {e}")

def test_error_message_format():
    """測試錯誤訊息格式"""
    print("\n" + "=" * 80)
    print("錯誤訊息格式測試")
    print("=" * 80)
    
    from error_messages import get_friendly_message, detect_error_type
    
    # 測試錯誤類型檢測
    test_cases = [
        "Category with name 'test' already exists",
        "Product code already exists",
        "Email already registered",
        "Category not found",
        "Product not found",
        "Database connection error",
        "Validation error occurred"
    ]
    
    print("\n錯誤類型檢測測試:")
    for case in test_cases:
        error_type = detect_error_type(case)
        friendly_msg = get_friendly_message(error_type)
        print(f"   原始: {case}")
        print(f"   類型: {error_type}")
        print(f"   友善: {friendly_msg}")
        print()

if __name__ == "__main__":
    print("統一錯誤處理系統測試工具")
    print("請確認後端服務正在運行 (http://localhost:8000)")
    
    choice = input("\n選擇測試類型 (1: API 錯誤測試, 2: 訊息格式測試, 3: 全部測試): ").strip()
    
    if choice == "1":
        test_error_handling()
    elif choice == "2":
        test_error_message_format()
    elif choice == "3":
        test_error_message_format()
        test_error_handling()
    else:
        print("無效的選擇")
