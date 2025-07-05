"""
檢查詳細的資料狀況
"""
from sqlalchemy import create_engine, text

# 資料庫連接
DATABASE_URL = "postgresql://postgres:123456@localhost:5432/inventory_db_fastapi"

def check_detailed_data():
    """檢查詳細的資料狀況"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as connection:
        try:
            print("=" * 100)
            print("詳細資料檢查報告")
            print("=" * 100)
            
            # 1. 檢查採購單
            print("\n1. 採購單資料：")
            po_result = connection.execute(text("""
                SELECT po_number, purchase_date, status, total_amount
                FROM purchase_orders
                ORDER BY po_number DESC
                LIMIT 5
            """)).fetchall()
            
            print(f"   {'採購單號':<20} {'採購日期':<12} {'狀態':<15} {'總金額':<10}")
            print("   " + "-" * 70)
            for row in po_result:
                print(f"   {row[0]:<20} {row[1]:<12} {row[2]:<15} {row[3]:<10}")
            
            # 2. 檢查採購單明細
            print("\n2. 採購單明細：")
            po_items_result = connection.execute(text("""
                SELECT po.po_number, p."productName", poi.quantity, poi.unit_price, poi.line_total
                FROM purchase_order_items poi
                JOIN purchase_orders po ON poi.purchase_order_id = po.id
                JOIN products p ON poi.product_id = p.id
                ORDER BY po.po_number DESC, poi.id
                LIMIT 10
            """)).fetchall()
            
            print(f"   {'採購單號':<20} {'產品名稱':<30} {'數量':<8} {'單價':<10} {'小計':<10}")
            print("   " + "-" * 90)
            for row in po_items_result:
                print(f"   {row[0]:<20} {row[1][:28]:<30} {row[2]:<8} {row[3]:<10} {row[4]:<10}")
            
            # 3. 檢查入庫單
            print("\n3. 入庫單資料：")
            gr_result = connection.execute(text("""
                SELECT gr_number, receipt_date, gr.status, po.po_number
                FROM goods_receipts gr
                JOIN purchase_orders po ON gr.purchase_order_id = po.id
                ORDER BY gr.gr_number DESC
                LIMIT 5
            """)).fetchall()
            
            print(f"   {'入庫單號':<20} {'入庫日期':<12} {'狀態':<15} {'採購單號':<20}")
            print("   " + "-" * 80)
            for row in gr_result:
                print(f"   {row[0]:<20} {row[1]:<12} {row[2]:<15} {row[3]:<20}")
            
            # 4. 檢查入庫單明細
            print("\n4. 入庫單明細：")
            gr_items_result = connection.execute(text("""
                SELECT gr.gr_number, p."productName", gri.ordered_quantity, gri.received_quantity
                FROM goods_receipt_items gri
                JOIN goods_receipts gr ON gri.goods_receipt_id = gr.id
                JOIN products p ON gri.product_id = p.id
                ORDER BY gr.gr_number DESC, gri.id
                LIMIT 10
            """)).fetchall()
            
            print(f"   {'入庫單號':<20} {'產品名稱':<30} {'訂購數量':<10} {'實收數量':<10}")
            print("   " + "-" * 80)
            for row in gr_items_result:
                print(f"   {row[0]:<20} {row[1][:28]:<30} {row[2]:<10} {row[3]:<10}")
            
            # 5. 檢查產品庫存
            print("\n5. 產品庫存：")
            product_result = connection.execute(text("""
                SELECT "productName", stock
                FROM products
                ORDER BY "productName"
            """)).fetchall()
            
            print(f"   {'產品名稱':<40} {'當前庫存':<10}")
            print("   " + "-" * 60)
            for row in product_result:
                print(f"   {row[0][:38]:<40} {row[1]:<10}")
            
            # 6. 檢查庫存計算
            print("\n6. 庫存計算詳細：")
            stock_calc_result = connection.execute(text("""
                SELECT 
                    p."productName",
                    p.stock as current_stock,
                    COALESCE(received.total_received, 0) as total_received,
                    COALESCE(shipped.total_shipped, 0) as total_shipped,
                    (COALESCE(received.total_received, 0) - COALESCE(shipped.total_shipped, 0)) as calculated_stock,
                    received.completed_receipts,
                    shipped.shipped_orders
                FROM products p
                LEFT JOIN (
                    SELECT 
                        gri.product_id,
                        SUM(gri.received_quantity) as total_received,
                        COUNT(DISTINCT gr.id) as completed_receipts
                    FROM goods_receipt_items gri
                    JOIN goods_receipts gr ON gri.goods_receipt_id = gr.id
                    WHERE gr.status = 'COMPLETED'
                    GROUP BY gri.product_id
                ) received ON p.id = received.product_id
                LEFT JOIN (
                    SELECT 
                        soi.product_id,
                        SUM(soi.quantity) as total_shipped,
                        COUNT(DISTINCT so.id) as shipped_orders
                    FROM sales_order_items soi
                    JOIN sales_orders so ON soi.sales_order_id = so.id
                    WHERE so.status = 'SHIPPED'
                    GROUP BY soi.product_id
                ) shipped ON p.id = shipped.product_id
                ORDER BY p."productName"
            """)).fetchall()
            
            print(f"   {'產品名稱':<30} {'當前庫存':<8} {'入庫總量':<8} {'出貨總量':<8} {'計算庫存':<8} {'入庫單數':<8} {'出貨單數':<8}")
            print("   " + "-" * 100)
            for row in stock_calc_result:
                product_name = row[0][:28] if row[0] else "N/A"
                current_stock = row[1] if row[1] is not None else 0
                total_received = row[2] if row[2] is not None else 0
                total_shipped = row[3] if row[3] is not None else 0
                calculated_stock = row[4] if row[4] is not None else 0
                completed_receipts = row[5] if row[5] is not None else 0
                shipped_orders = row[6] if row[6] is not None else 0
                
                print(f"   {product_name:<30} {current_stock:<8} {total_received:<8} {total_shipped:<8} {calculated_stock:<8} {completed_receipts:<8} {shipped_orders:<8}")
            
            # 7. 檢查入庫單狀態變更歷史（如果有的話）
            print("\n7. 最近的入庫單狀態：")
            recent_gr_result = connection.execute(text("""
                SELECT gr.gr_number, gr.status, gr.created_at, gr.updated_at
                FROM goods_receipts gr
                ORDER BY gr.created_at DESC
                LIMIT 5
            """)).fetchall()
            
            print(f"   {'入庫單號':<20} {'狀態':<15} {'建立時間':<20} {'更新時間':<20}")
            print("   " + "-" * 80)
            for row in recent_gr_result:
                created_at = str(row[2])[:19] if row[2] else "N/A"
                updated_at = str(row[3])[:19] if row[3] else "N/A"
                print(f"   {row[0]:<20} {row[1]:<15} {created_at:<20} {updated_at:<20}")
            
            print("\n" + "=" * 100)
            print("檢查完成")
            print("=" * 100)
            
        except Exception as e:
            print(f"❌ 檢查時發生錯誤: {e}")

if __name__ == "__main__":
    check_detailed_data()
