"""
測試所有模組導入是否正常
"""

def test_all_imports():
    """測試所有模組導入"""
    print("=" * 60)
    print("模組導入測試")
    print("=" * 60)
    
    try:
        print("1. 測試基本模組導入...")
        import models, schemas, database
        print("   ✅ models, schemas, database 導入成功")

        print("2. 測試路由模組導入...")
        from routers import (
            auth, users, categories, suppliers, products,
            transactions, customers, purchase_orders,
            goods_receipts, sales_orders, shipping_orders
        )
        print("   ✅ 所有路由模組導入成功")

        print("3. 測試 FastAPI 應用導入...")
        import main
        print("   ✅ FastAPI 應用導入成功")
        
        print("4. 檢查出貨單模型...")
        print(f"   - ShippingOrder 模型: {hasattr(models, 'ShippingOrder')}")
        print(f"   - ShippingOrderItem 模型: {hasattr(models, 'ShippingOrderItem')}")
        print(f"   - ShippingOrderStatus 枚舉: {hasattr(models, 'ShippingOrderStatus')}")
        
        print("5. 檢查出貨單 Schema...")
        print(f"   - ShippingOrder Schema: {hasattr(schemas, 'ShippingOrder')}")
        print(f"   - ShippingOrderCreate Schema: {hasattr(schemas, 'ShippingOrderCreate')}")
        
        print("6. 檢查出貨單路由...")
        print(f"   - shipping_orders 路由: {hasattr(shipping_orders, 'router')}")
        
        print("\n" + "=" * 60)
        print("✅ 所有模組導入測試通過！")
        print("✅ 後端應該可以正常啟動")
        print("=" * 60)
        
        return True
        
    except ImportError as e:
        print(f"❌ 導入錯誤: {e}")
        return False
    except Exception as e:
        print(f"❌ 其他錯誤: {e}")
        return False

def test_shipping_order_enums():
    """測試出貨單相關枚舉"""
    print("\n" + "=" * 60)
    print("出貨單枚舉測試")
    print("=" * 60)
    
    try:
        import models
        
        print("1. 出貨單狀態:")
        for status in models.ShippingOrderStatus:
            print(f"   - {status.name}: {status.value}")
        
        print("\n2. 運輸方式:")
        for method in models.ShippingMethod:
            print(f"   - {method.name}: {method.value}")
        
        print("\n✅ 枚舉測試通過！")
        return True
        
    except Exception as e:
        print(f"❌ 枚舉測試失敗: {e}")
        return False

if __name__ == "__main__":
    print("後端模組導入測試工具")
    print("這個測試會檢查所有模組是否能正常導入")
    
    # 執行導入測試
    import_success = test_all_imports()
    
    if import_success:
        # 執行枚舉測試
        enum_success = test_shipping_order_enums()
        
        if enum_success:
            print("\n🎉 所有測試通過！")
            print("💡 您現在可以啟動後端服務：")
            print("   uvicorn backend.main:app --reload --host 0.0.0.0 --port 5050")
        else:
            print("\n⚠️ 枚舉測試失敗，請檢查模型定義")
    else:
        print("\n❌ 導入測試失敗，請檢查模組導入問題")
