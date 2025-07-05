"""
測試 Transaction 系統整合 ERP 系統的功能
"""
import requests
import json
from datetime import date

# API 基礎 URL
BASE_URL = "http://localhost:8000/api"

def test_transaction_integration():
    """測試交易系統整合"""
    print("=" * 80)
    print("交易系統整合測試")
    print("=" * 80)
    
    try:
        # 1. 測試獲取所有交易（應該包含 ERP 系統的交易）
        print("\n1. 測試獲取所有交易:")
        response = requests.get(f"{BASE_URL}/transactions/all")
        print(f"   狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            transactions = response.json()
            print(f"   交易總數: {len(transactions)}")
            
            # 分析交易來源
            original_transactions = [t for t in transactions if t['id'] < 1000000]
            purchase_transactions = [t for t in transactions if t['id'] > 1000000 and t['id'] % 1000000 == 1]
            sales_transactions = [t for t in transactions if t['id'] > 1000000 and t['id'] % 1000000 == 2]
            
            print(f"   原有交易記錄: {len(original_transactions)}")
            print(f"   採購單轉換交易: {len(purchase_transactions)}")
            print(f"   銷售單轉換交易: {len(sales_transactions)}")
            
            # 顯示前幾筆交易
            print("\n   前5筆交易:")
            for i, transaction in enumerate(transactions[:5]):
                transaction_type = "原有"
                if transaction['id'] > 1000000:
                    if transaction['id'] % 1000000 == 1:
                        transaction_type = "採購單"
                    elif transaction['id'] % 1000000 == 2:
                        transaction_type = "銷售單"
                
                print(f"   {i+1}. ID: {transaction['id']} ({transaction_type}) - {transaction['description']} - {transaction['transactionType']} - {transaction['transactionStatus']}")
            
            # 2. 測試查詢單個交易
            if transactions:
                test_transaction = transactions[0]
                print(f"\n2. 測試查詢單個交易 (ID: {test_transaction['id']}):")
                response = requests.get(f"{BASE_URL}/transactions/{test_transaction['id']}")
                print(f"   狀態碼: {response.status_code}")
                
                if response.status_code == 200:
                    transaction_detail = response.json()
                    print(f"   交易描述: {transaction_detail['description']}")
                    print(f"   交易類型: {transaction_detail['transactionType']}")
                    print(f"   交易狀態: {transaction_detail['transactionStatus']}")
                    print(f"   總金額: {transaction_detail['totalPrice']}")
                    print(f"   總產品數: {transaction_detail['totalProducts']}")
                    print(f"   產品明細數量: {len(transaction_detail.get('products', []))}")
                else:
                    print(f"   錯誤: {response.text}")
            
            # 3. 測試搜尋功能
            print("\n3. 測試搜尋功能:")
            search_terms = ["採購", "銷售", "PO-", "SO-"]
            
            for term in search_terms:
                response = requests.get(f"{BASE_URL}/transactions/all?searchText={term}")
                if response.status_code == 200:
                    search_results = response.json()
                    print(f"   搜尋 '{term}': 找到 {len(search_results)} 筆記錄")
                else:
                    print(f"   搜尋 '{term}' 失敗: {response.text}")
            
            # 4. 測試狀態更新（如果有可更新的交易）
            updatable_transactions = [t for t in transactions if t['transactionStatus'] == 'COMPLETED']
            if updatable_transactions:
                test_transaction = updatable_transactions[0]
                print(f"\n4. 測試狀態更新 (ID: {test_transaction['id']}):")
                
                # 先嘗試更新為 PENDING
                status_data = {"status": "PENDING"}
                response = requests.put(
                    f"{BASE_URL}/transactions/update/{test_transaction['id']}",
                    json=status_data
                )
                print(f"   更新為 PENDING - 狀態碼: {response.status_code}")
                
                if response.status_code == 200:
                    updated_transaction = response.json()
                    print(f"   新狀態: {updated_transaction['transactionStatus']}")
                    
                    # 再更新回 COMPLETED
                    status_data = {"status": "COMPLETED"}
                    response = requests.put(
                        f"{BASE_URL}/transactions/update/{test_transaction['id']}",
                        json=status_data
                    )
                    print(f"   更新回 COMPLETED - 狀態碼: {response.status_code}")
                else:
                    print(f"   更新失敗: {response.text}")
            else:
                print("\n4. 沒有可更新的交易記錄")
        
        else:
            print(f"   錯誤: {response.text}")
        
        print("\n" + "=" * 80)
        print("測試完成")
        print("=" * 80)
        
    except requests.exceptions.ConnectionError:
        print("❌ 無法連接到後端服務，請確認後端是否正在運行")
    except Exception as e:
        print(f"❌ 測試時發生錯誤: {e}")

def test_erp_system_status():
    """檢查 ERP 系統狀態"""
    print("\n" + "=" * 80)
    print("ERP 系統狀態檢查")
    print("=" * 80)
    
    try:
        # 檢查採購單
        print("\n1. 檢查採購單狀態:")
        response = requests.get(f"{BASE_URL}/purchase-orders/")
        if response.status_code == 200:
            purchase_orders = response.json()
            received_pos = [po for po in purchase_orders if po.get('status') == 'RECEIVED']
            print(f"   總採購單數: {len(purchase_orders)}")
            print(f"   已收貨採購單: {len(received_pos)}")
            
            if received_pos:
                print("   已收貨採購單:")
                for po in received_pos[:3]:
                    print(f"   - {po.get('po_number', 'N/A')}: {po.get('total_amount', 0)}")
        else:
            print(f"   無法獲取採購單: {response.text}")
        
        # 檢查銷售單
        print("\n2. 檢查銷售單狀態:")
        response = requests.get(f"{BASE_URL}/sales-orders/")
        if response.status_code == 200:
            sales_orders = response.json()
            shipped_sos = [so for so in sales_orders if so.get('status') in ['SHIPPED', 'DELIVERED']]
            print(f"   總銷售單數: {len(sales_orders)}")
            print(f"   已出貨銷售單: {len(shipped_sos)}")
            
            if shipped_sos:
                print("   已出貨銷售單:")
                for so in shipped_sos[:3]:
                    print(f"   - {so.get('so_number', 'N/A')}: {so.get('total_amount', 0)}")
        else:
            print(f"   無法獲取銷售單: {response.text}")
            
    except Exception as e:
        print(f"❌ ERP 系統檢查時發生錯誤: {e}")

if __name__ == "__main__":
    print("交易系統整合測試工具")
    print("請確認後端服務正在運行 (http://localhost:8000)")
    
    choice = input("\n選擇測試類型 (1: 交易整合測試, 2: ERP 系統狀態, 3: 全部測試): ").strip()
    
    if choice == "1":
        test_transaction_integration()
    elif choice == "2":
        test_erp_system_status()
    elif choice == "3":
        test_erp_system_status()
        test_transaction_integration()
    else:
        print("無效的選擇")
