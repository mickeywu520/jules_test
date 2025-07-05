"""
簡單的庫存檢查腳本
"""
from sqlalchemy import create_engine, text

# 資料庫連接
DATABASE_URL = "postgresql://postgres:123456@localhost:5432/inventory_db_fastapi"

def check_stock_accuracy():
    """檢查庫存準確性"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as connection:
        try:
            # 獲取庫存摘要
            result = connection.execute(text("""
                SELECT
                    p."productName",
                    p.stock as current_stock,
                    COALESCE(received.total_received, 0) as total_received,
                    COALESCE(shipped.total_shipped, 0) as total_shipped,
                    (COALESCE(received.total_received, 0) - COALESCE(shipped.total_shipped, 0)) as calculated_stock
                FROM products p
                LEFT JOIN (
                    SELECT 
                        gri.product_id,
                        SUM(gri.received_quantity) as total_received
                    FROM goods_receipt_items gri
                    JOIN goods_receipts gr ON gri.goods_receipt_id = gr.id
                    WHERE gr.status = 'COMPLETED'
                    GROUP BY gri.product_id
                ) received ON p.id = received.product_id
                LEFT JOIN (
                    SELECT 
                        soi.product_id,
                        SUM(soi.quantity) as total_shipped
                    FROM sales_order_items soi
                    JOIN sales_orders so ON soi.sales_order_id = so.id
                    WHERE so.status = 'SHIPPED'
                    GROUP BY soi.product_id
                ) shipped ON p.id = shipped.product_id
                ORDER BY p."productName"
            """)).fetchall()
            
            print("=" * 100)
            print("庫存準確性檢查報告")
            print("=" * 100)
            print(f"{'產品名稱':<30} {'當前庫存':<10} {'入庫總量':<10} {'出貨總量':<10} {'計算庫存':<10} {'差異':<10} {'狀態':<10}")
            print("-" * 100)
            
            total_diff = 0
            problem_count = 0
            
            for row in result:
                product_name = row[0][:28]  # 截斷長名稱
                current_stock = row[1]
                total_received = row[2]
                total_shipped = row[3]
                calculated_stock = row[4]
                diff = current_stock - calculated_stock
                total_diff += abs(diff)
                
                if diff != 0:
                    problem_count += 1
                    status = "❌ 錯誤"
                else:
                    status = "✅ 正確"
                
                print(f"{product_name:<30} {current_stock:<10} {total_received:<10} {total_shipped:<10} {calculated_stock:<10} {diff:<10} {status:<10}")
            
            print("-" * 100)
            print(f"總產品數量: {len(result)}")
            print(f"有問題的產品: {problem_count}")
            print(f"總差異數量: {total_diff}")
            
            if total_diff == 0:
                print("✅ 所有產品庫存都是正確的！")
            else:
                print("❌ 發現庫存差異，需要修正")
                print("\n建議執行以下 SQL 來修正庫存：")
                print("UPDATE products SET stock = (")
                print("  SELECT COALESCE(received.total_received, 0) - COALESCE(shipped.total_shipped, 0)")
                print("  FROM (")
                print("    SELECT product_id, SUM(received_quantity) as total_received")
                print("    FROM goods_receipt_items gri")
                print("    JOIN goods_receipts gr ON gri.goods_receipt_id = gr.id")
                print("    WHERE gr.status = 'COMPLETED'")
                print("    GROUP BY product_id")
                print("  ) received")
                print("  LEFT JOIN (")
                print("    SELECT product_id, SUM(quantity) as total_shipped")
                print("    FROM sales_order_items soi")
                print("    JOIN sales_orders so ON soi.sales_order_id = so.id")
                print("    WHERE so.status = 'SHIPPED'")
                print("    GROUP BY product_id")
                print("  ) shipped ON received.product_id = shipped.product_id")
                print("  WHERE received.product_id = products.id")
                print(");")
            
        except Exception as e:
            print(f"❌ 檢查庫存時發生錯誤: {e}")

def fix_stock():
    """修正所有產品的庫存"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as connection:
        try:
            # 執行庫存修正
            result = connection.execute(text("""
                UPDATE products SET stock = COALESCE((
                    SELECT COALESCE(received.total_received, 0) - COALESCE(shipped.total_shipped, 0)
                    FROM (
                        SELECT 
                            gri.product_id,
                            SUM(gri.received_quantity) as total_received
                        FROM goods_receipt_items gri
                        JOIN goods_receipts gr ON gri.goods_receipt_id = gr.id
                        WHERE gr.status = 'COMPLETED'
                        GROUP BY gri.product_id
                    ) received
                    LEFT JOIN (
                        SELECT 
                            soi.product_id,
                            SUM(soi.quantity) as total_shipped
                        FROM sales_order_items soi
                        JOIN sales_orders so ON soi.sales_order_id = so.id
                        WHERE so.status = 'SHIPPED'
                        GROUP BY soi.product_id
                    ) shipped ON received.product_id = shipped.product_id
                    WHERE received.product_id = products.id
                ), 0)
            """))
            
            connection.commit()
            print(f"✅ 已修正 {result.rowcount} 個產品的庫存")
            
        except Exception as e:
            print(f"❌ 修正庫存時發生錯誤: {e}")
            connection.rollback()

if __name__ == "__main__":
    print("庫存管理工具")
    print("1. 檢查庫存準確性")
    print("2. 修正所有庫存")
    
    choice = input("請選擇操作 (1 或 2): ").strip()
    
    if choice == "1":
        check_stock_accuracy()
    elif choice == "2":
        print("⚠️  這將重新計算並修正所有產品的庫存，確定要繼續嗎？")
        confirm = input("輸入 'yes' 確認: ").strip().lower()
        if confirm == "yes":
            fix_stock()
            print("\n修正完成，重新檢查庫存：")
            check_stock_accuracy()
        else:
            print("操作已取消")
    else:
        print("無效的選擇")
