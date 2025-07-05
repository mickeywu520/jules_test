"""
測試產品軟刪除功能
"""
import requests
import json

# API 基礎 URL
BASE_URL = "http://localhost:8000/api"

def test_soft_delete():
    """測試軟刪除功能"""
    print("=" * 80)
    print("產品軟刪除功能測試")
    print("=" * 80)
    
    try:
        # 1. 先獲取類別列表
        print("\n1. 獲取類別列表:")
        categories_response = requests.get(f"{BASE_URL}/categories/all")
        if categories_response.status_code != 200:
            print("   無法獲取類別列表，請先創建類別")
            return
        
        categories = categories_response.json()
        if not categories:
            print("   沒有可用的類別，請先創建類別")
            return
        
        category_id = categories[0]['id']
        print(f"   使用類別 ID: {category_id}")
        
        # 2. 創建測試產品
        print("\n2. 創建測試產品:")
        product_data = {
            "productCode": "SOFT_DELETE_TEST_001",
            "productName": "軟刪除測試產品",
            "unit": "個",
            "category_id": category_id
        }
        
        response = requests.post(f"{BASE_URL}/products/add", json=product_data)
        print(f"   創建產品 - 狀態碼: {response.status_code}")
        
        if response.status_code != 200:
            print(f"   創建失敗: {response.text}")
            return
        
        product = response.json()
        product_id = product['id']
        print(f"   產品 ID: {product_id}")
        print(f"   產品編號: {product['productCode']}")
        print(f"   是否已刪除: {product.get('is_deleted', 'N/A')}")
        
        # 3. 確認產品在列表中
        print("\n3. 確認產品在列表中:")
        response = requests.get(f"{BASE_URL}/products/all")
        if response.status_code == 200:
            products = response.json()
            test_product = next((p for p in products if p['id'] == product_id), None)
            if test_product:
                print(f"   ✅ 產品在列表中: {test_product['productName']}")
            else:
                print("   ❌ 產品不在列表中")
        
        # 4. 軟刪除產品
        print("\n4. 軟刪除產品:")
        response = requests.delete(f"{BASE_URL}/products/delete/{product_id}")
        print(f"   刪除產品 - 狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            deleted_product = response.json()
            print(f"   刪除成功")
            print(f"   是否已刪除: {deleted_product.get('is_deleted', 'N/A')}")
            print(f"   刪除時間: {deleted_product.get('deleted_at', 'N/A')}")
        else:
            print(f"   刪除失敗: {response.text}")
            return
        
        # 5. 確認產品不在一般列表中
        print("\n5. 確認產品不在一般列表中:")
        response = requests.get(f"{BASE_URL}/products/all")
        if response.status_code == 200:
            products = response.json()
            test_product = next((p for p in products if p['id'] == product_id), None)
            if test_product:
                print("   ❌ 產品仍在列表中（軟刪除失敗）")
            else:
                print("   ✅ 產品已從列表中移除")
        
        # 6. 確認產品在已刪除列表中
        print("\n6. 確認產品在已刪除列表中:")
        response = requests.get(f"{BASE_URL}/products/deleted/all")
        if response.status_code == 200:
            deleted_products = response.json()
            test_product = next((p for p in deleted_products if p['id'] == product_id), None)
            if test_product:
                print(f"   ✅ 產品在已刪除列表中: {test_product['productName']}")
                print(f"   刪除狀態: {test_product.get('is_deleted', 'N/A')}")
            else:
                print("   ❌ 產品不在已刪除列表中")
        else:
            print(f"   無法獲取已刪除列表: {response.text}")
        
        # 7. 測試創建相同編號的新產品
        print("\n7. 測試創建相同編號的新產品:")
        new_product_data = {
            "productCode": "SOFT_DELETE_TEST_001",  # 相同編號
            "productName": "新的測試產品",
            "unit": "盒",
            "category_id": category_id
        }
        
        response = requests.post(f"{BASE_URL}/products/add", json=new_product_data)
        print(f"   創建相同編號產品 - 狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            new_product = response.json()
            print(f"   ✅ 成功創建新產品")
            print(f"   新產品 ID: {new_product['id']}")
            print(f"   新產品名稱: {new_product['productName']}")
            new_product_id = new_product['id']
        else:
            print(f"   創建失敗: {response.text}")
            new_product_id = None
        
        # 8. 測試恢復已刪除的產品（應該失敗，因為編號衝突）
        print("\n8. 測試恢復已刪除的產品:")
        response = requests.patch(f"{BASE_URL}/products/restore/{product_id}")
        print(f"   恢復產品 - 狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            print("   ❌ 恢復成功（不應該成功，因為編號衝突）")
        else:
            error_data = response.json()
            print(f"   ✅ 恢復失敗（預期結果）: {error_data.get('message', 'N/A')}")
        
        # 9. 刪除新產品，然後恢復舊產品
        if new_product_id:
            print("\n9. 刪除新產品，然後恢復舊產品:")
            
            # 刪除新產品
            response = requests.delete(f"{BASE_URL}/products/delete/{new_product_id}")
            print(f"   刪除新產品 - 狀態碼: {response.status_code}")
            
            # 恢復舊產品
            response = requests.patch(f"{BASE_URL}/products/restore/{product_id}")
            print(f"   恢復舊產品 - 狀態碼: {response.status_code}")
            
            if response.status_code == 200:
                restored_product = response.json()
                print(f"   ✅ 恢復成功")
                print(f"   是否已刪除: {restored_product.get('is_deleted', 'N/A')}")
                print(f"   刪除時間: {restored_product.get('deleted_at', 'N/A')}")
            else:
                print(f"   恢復失敗: {response.text}")
        
        print("\n" + "=" * 80)
        print("軟刪除測試完成")
        print("=" * 80)
        
    except requests.exceptions.ConnectionError:
        print("❌ 無法連接到後端服務，請確認後端是否正在運行")
    except Exception as e:
        print(f"❌ 測試時發生錯誤: {e}")

def test_foreign_key_scenario():
    """測試有外鍵關聯的軟刪除場景"""
    print("\n" + "=" * 80)
    print("外鍵關聯軟刪除測試")
    print("=" * 80)
    
    try:
        # 這個測試需要先有採購單或銷售單資料
        # 可以手動創建一些測試資料，然後測試軟刪除
        print("此測試需要手動創建採購單/銷售單資料")
        print("然後測試軟刪除有關聯的產品")
        
    except Exception as e:
        print(f"❌ 測試時發生錯誤: {e}")

if __name__ == "__main__":
    print("產品軟刪除功能測試工具")
    print("請確認後端服務正在運行 (http://localhost:8000)")
    
    choice = input("\n選擇測試類型 (1: 軟刪除測試, 2: 外鍵關聯測試, 3: 全部測試): ").strip()
    
    if choice == "1":
        test_soft_delete()
    elif choice == "2":
        test_foreign_key_scenario()
    elif choice == "3":
        test_soft_delete()
        test_foreign_key_scenario()
    else:
        print("無效的選擇")
