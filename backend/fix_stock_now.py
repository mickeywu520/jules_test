"""
立即修正庫存
"""
from sqlalchemy import create_engine, text

# 資料庫連接
DATABASE_URL = "postgresql://postgres:123456@localhost:5432/inventory_db_fastapi"

def fix_stock_immediately():
    """立即修正庫存"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as connection:
        try:
            print("正在修正庫存...")
            
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
            
            # 檢查修正結果
            check_result = connection.execute(text("""
                SELECT 
                    p."productName",
                    p.stock as current_stock,
                    COALESCE(received.total_received, 0) as total_received,
                    COALESCE(shipped.total_shipped, 0) as total_shipped
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
            
            print("\n修正後的庫存狀況：")
            print(f"{'產品名稱':<40} {'當前庫存':<10} {'入庫總量':<10} {'出貨總量':<10}")
            print("-" * 80)
            for row in check_result:
                product_name = row[0][:38] if row[0] else "N/A"
                current_stock = row[1] if row[1] is not None else 0
                total_received = row[2] if row[2] is not None else 0
                total_shipped = row[3] if row[3] is not None else 0
                
                print(f"{product_name:<40} {current_stock:<10} {total_received:<10} {total_shipped:<10}")
            
        except Exception as e:
            print(f"❌ 修正庫存時發生錯誤: {e}")
            connection.rollback()

if __name__ == "__main__":
    fix_stock_immediately()
