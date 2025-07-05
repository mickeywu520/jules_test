"""
測試出貨單 API
"""
import requests
import json
from datetime import date

# API 基礎 URL
BASE_URL = "http://localhost:8000/api"

def test_shipping_orders_api():
    """測試出貨單 API"""
    print("=" * 80)
    print("出貨單 API 測試")
    print("=" * 80)
    
    try:
        # 1. 測試獲取所有出貨單
        print("\n1. 測試獲取所有出貨單:")
        response = requests.get(f"{BASE_URL}/shipping-orders/")
        print(f"   狀態碼: {response.status_code}")
        if response.status_code == 200:
            shipping_orders = response.json()
            print(f"   出貨單數量: {len(shipping_orders)}")
            for so in shipping_orders[:3]:  # 只顯示前3筆
                print(f"   - {so.get('sh_number', 'N/A')}: {so.get('status', 'N/A')}")
        else:
            print(f"   錯誤: {response.text}")
        
        # 2. 測試獲取銷售單列表（用於創建出貨單）
        print("\n2. 測試獲取銷售單列表:")
        response = requests.get(f"{BASE_URL}/sales-orders/")
        print(f"   狀態碼: {response.status_code}")
        if response.status_code == 200:
            sales_orders = response.json()
            print(f"   銷售單數量: {len(sales_orders)}")
            
            # 找到已確認的銷售單
            confirmed_sales_orders = [so for so in sales_orders if so.get('status') == 'CONFIRMED']
            print(f"   已確認的銷售單數量: {len(confirmed_sales_orders)}")
            
            if confirmed_sales_orders:
                test_sales_order = confirmed_sales_orders[0]
                print(f"   測試用銷售單: {test_sales_order.get('so_number', 'N/A')}")
                
                # 3. 測試基於銷售單創建出貨單
                print("\n3. 測試基於銷售單創建出貨單:")
                shipping_data = {
                    "shipping_date": str(date.today()),
                    "shipping_address": "測試出貨地址",
                    "shipper_name": "測試出貨員",
                    "shipping_method": "SELF_DELIVERY",
                    "tracking_number": "TEST123456",
                    "notes": "測試出貨單"
                }
                
                response = requests.post(
                    f"{BASE_URL}/shipping-orders/from-sales-order/{test_sales_order['id']}",
                    json=shipping_data
                )
                print(f"   狀態碼: {response.status_code}")
                if response.status_code == 200:
                    new_shipping_order = response.json()
                    print(f"   新出貨單號: {new_shipping_order.get('sh_number', 'N/A')}")
                    print(f"   狀態: {new_shipping_order.get('status', 'N/A')}")
                    print(f"   明細數量: {len(new_shipping_order.get('items', []))}")
                    
                    shipping_order_id = new_shipping_order['id']
                    
                    # 4. 測試獲取出貨單詳情
                    print("\n4. 測試獲取出貨單詳情:")
                    response = requests.get(f"{BASE_URL}/shipping-orders/{shipping_order_id}")
                    print(f"   狀態碼: {response.status_code}")
                    if response.status_code == 200:
                        shipping_order = response.json()
                        print(f"   出貨單號: {shipping_order.get('sh_number', 'N/A')}")
                        print(f"   客戶: {shipping_order.get('customer', {}).get('customerName', 'N/A')}")
                        print(f"   出貨地址: {shipping_order.get('shipping_address', 'N/A')}")
                    
                    # 5. 測試更新出貨單狀態
                    print("\n5. 測試更新出貨單狀態:")
                    status_data = {"status": "READY"}
                    response = requests.patch(
                        f"{BASE_URL}/shipping-orders/{shipping_order_id}/status",
                        json=status_data
                    )
                    print(f"   狀態碼: {response.status_code}")
                    if response.status_code == 200:
                        result = response.json()
                        print(f"   更新結果: {result.get('message', 'N/A')}")
                        print(f"   新狀態: {result.get('status', 'N/A')}")
                    else:
                        print(f"   錯誤: {response.text}")
                    
                    # 6. 測試更新出貨單
                    print("\n6. 測試更新出貨單:")
                    update_data = {
                        "shipper_name": "更新後的出貨員",
                        "notes": "更新後的備註"
                    }
                    response = requests.put(
                        f"{BASE_URL}/shipping-orders/{shipping_order_id}",
                        json=update_data
                    )
                    print(f"   狀態碼: {response.status_code}")
                    if response.status_code == 200:
                        updated_shipping_order = response.json()
                        print(f"   更新後出貨員: {updated_shipping_order.get('shipper_name', 'N/A')}")
                        print(f"   更新後備註: {updated_shipping_order.get('notes', 'N/A')}")
                    else:
                        print(f"   錯誤: {response.text}")
                    
                    # 7. 測試刪除出貨單（如果狀態允許）
                    print("\n7. 測試刪除出貨單:")
                    response = requests.delete(f"{BASE_URL}/shipping-orders/{shipping_order_id}")
                    print(f"   狀態碼: {response.status_code}")
                    if response.status_code == 200:
                        result = response.json()
                        print(f"   刪除結果: {result.get('message', 'N/A')}")
                    else:
                        print(f"   錯誤: {response.text}")
                        print("   (可能是因為狀態不允許刪除)")
                
                else:
                    print(f"   錯誤: {response.text}")
            else:
                print("   沒有已確認的銷售單可用於測試")
        else:
            print(f"   錯誤: {response.text}")
        
        print("\n" + "=" * 80)
        print("測試完成")
        print("=" * 80)
        
    except requests.exceptions.ConnectionError:
        print("❌ 無法連接到後端服務，請確認後端是否正在運行")
    except Exception as e:
        print(f"❌ 測試時發生錯誤: {e}")

def test_shipping_order_status_flow():
    """測試出貨單狀態流程"""
    print("\n" + "=" * 80)
    print("出貨單狀態流程測試")
    print("=" * 80)
    
    try:
        # 獲取第一個出貨單進行狀態測試
        response = requests.get(f"{BASE_URL}/shipping-orders/")
        if response.status_code == 200:
            shipping_orders = response.json()
            if shipping_orders:
                shipping_order = shipping_orders[0]
                shipping_order_id = shipping_order['id']
                print(f"測試出貨單: {shipping_order.get('sh_number', 'N/A')}")
                print(f"當前狀態: {shipping_order.get('status', 'N/A')}")
                
                # 測試狀態流程
                status_flow = ["PREPARING", "READY", "SHIPPED", "DELIVERED"]
                
                for status in status_flow:
                    print(f"\n嘗試更新狀態為: {status}")
                    status_data = {"status": status}
                    response = requests.patch(
                        f"{BASE_URL}/shipping-orders/{shipping_order_id}/status",
                        json=status_data
                    )
                    print(f"狀態碼: {response.status_code}")
                    if response.status_code == 200:
                        result = response.json()
                        print(f"✅ 成功: {result.get('message', 'N/A')}")
                    else:
                        print(f"❌ 失敗: {response.text}")
            else:
                print("沒有出貨單可用於測試")
        else:
            print(f"無法獲取出貨單列表: {response.text}")
            
    except Exception as e:
        print(f"❌ 狀態流程測試時發生錯誤: {e}")

if __name__ == "__main__":
    print("出貨單 API 測試工具")
    print("請確認後端服務正在運行 (http://localhost:8000)")
    
    choice = input("\n選擇測試類型 (1: 基本 API 測試, 2: 狀態流程測試, 3: 全部測試): ").strip()
    
    if choice == "1":
        test_shipping_orders_api()
    elif choice == "2":
        test_shipping_order_status_flow()
    elif choice == "3":
        test_shipping_orders_api()
        test_shipping_order_status_flow()
    else:
        print("無效的選擇")
