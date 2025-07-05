#!/usr/bin/env python3
"""
資料庫重建腳本
用於應用新的模型更改，包括 TransactionProductAssociation 的新欄位
"""

import os
import sys
from sqlalchemy import create_engine, text
from database import DATABASE_URL, Base
import models

def rebuild_database():
    """重建資料庫，應用所有模型更改"""
    print("開始重建資料庫...")
    
    # 創建引擎
    engine = create_engine(DATABASE_URL)
    
    try:
        # 刪除所有現有表格
        print("正在刪除現有表格...")
        Base.metadata.drop_all(bind=engine)
        print("現有表格已刪除")
        
        # 重新創建所有表格
        print("正在創建新表格...")
        Base.metadata.create_all(bind=engine)
        print("新表格已創建")
        
        # 驗證表格創建
        with engine.connect() as conn:
            # 檢查 transaction_product_association 表格是否有新欄位
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'transaction_product_association'
                ORDER BY column_name
            """))
            columns = [row[0] for row in result]
            print(f"transaction_product_association 表格欄位: {columns}")
            
            # 檢查 transactions 表格是否有 customer_id 欄位
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'transactions'
                ORDER BY column_name
            """))
            columns = [row[0] for row in result]
            print(f"transactions 表格欄位: {columns}")
        
        print("資料庫重建完成！")
        return True
        
    except Exception as e:
        print(f"資料庫重建失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = rebuild_database()
    if success:
        print("✅ 資料庫重建成功")
        sys.exit(0)
    else:
        print("❌ 資料庫重建失敗")
        sys.exit(1)
