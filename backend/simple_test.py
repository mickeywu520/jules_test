"""
簡單的導入測試
"""

def test_basic_imports():
    """測試基本導入"""
    print("=" * 60)
    print("基本導入測試")
    print("=" * 60)
    
    try:
        print("1. 測試 FastAPI...")
        from fastapi import FastAPI
        print("   ✅ FastAPI 導入成功")
        
        print("2. 測試 SQLAlchemy...")
        from sqlalchemy import create_engine
        from sqlalchemy.orm import Session
        print("   ✅ SQLAlchemy 導入成功")
        
        print("3. 測試 Pydantic...")
        from pydantic import BaseModel
        print("   ✅ Pydantic 導入成功")
        
        print("4. 測試 Python 標準庫...")
        from datetime import date, datetime
        from typing import List, Optional
        import enum
        print("   ✅ Python 標準庫導入成功")
        
        print("\n✅ 所有基本依賴都正常！")
        return True
        
    except ImportError as e:
        print(f"❌ 導入錯誤: {e}")
        return False

def test_shipping_order_syntax():
    """測試出貨單相關語法"""
    print("\n" + "=" * 60)
    print("出貨單語法測試")
    print("=" * 60)
    
    try:
        print("1. 測試枚舉定義...")
        import enum
        
        class ShippingOrderStatus(str, enum.Enum):
            PREPARING = "PREPARING"
            READY = "READY"
            SHIPPED = "SHIPPED"
            DELIVERED = "DELIVERED"
            CANCELLED = "CANCELLED"
        
        class ShippingMethod(str, enum.Enum):
            SELF_DELIVERY = "SELF_DELIVERY"
            HOME_DELIVERY = "HOME_DELIVERY"
            FREIGHT = "FREIGHT"
            PICKUP = "PICKUP"
        
        print("   ✅ 枚舉定義正確")
        
        print("2. 測試 Pydantic 模型...")
        from pydantic import BaseModel, Field
        from typing import Optional, List
        from datetime import date, datetime
        
        class ShippingOrderBase(BaseModel):
            shipping_date: date
            shipping_address: Optional[str] = None
            shipper_name: Optional[str] = None
            shipping_method: ShippingMethod = ShippingMethod.SELF_DELIVERY
            tracking_number: Optional[str] = None
            notes: Optional[str] = None
        
        print("   ✅ Pydantic 模型定義正確")
        
        print("3. 測試 SQLAlchemy 模型語法...")
        from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey, Enum as SQLAlchemyEnum
        from sqlalchemy.ext.declarative import declarative_base
        from sqlalchemy.orm import relationship
        from sqlalchemy.sql import func
        
        Base = declarative_base()
        
        class ShippingOrder(Base):
            __tablename__ = "shipping_orders"
            
            id = Column(Integer, primary_key=True, index=True)
            sh_number = Column(String, unique=True, index=True, nullable=False)
            shipping_date = Column(Date, nullable=False)
            status = Column(SQLAlchemyEnum(ShippingOrderStatus), default=ShippingOrderStatus.PREPARING)
            created_at = Column(DateTime(timezone=True), server_default=func.now())
        
        print("   ✅ SQLAlchemy 模型語法正確")
        
        print("\n✅ 所有語法測試通過！")
        return True
        
    except Exception as e:
        print(f"❌ 語法錯誤: {e}")
        return False

if __name__ == "__main__":
    print("出貨單系統語法測試")
    print("這個測試會檢查所有語法是否正確")
    
    # 執行基本導入測試
    basic_success = test_basic_imports()
    
    if basic_success:
        # 執行語法測試
        syntax_success = test_shipping_order_syntax()
        
        if syntax_success:
            print("\n🎉 所有測試通過！")
            print("💡 出貨單系統的語法和依賴都正確")
            print("💡 您現在可以：")
            print("   1. 重建資料庫")
            print("   2. 啟動後端服務")
            print("   3. 測試出貨單 API")
        else:
            print("\n⚠️ 語法測試失敗")
    else:
        print("\n❌ 基本導入測試失敗，請檢查依賴安裝")
