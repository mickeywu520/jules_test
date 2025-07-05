"""
重新計算所有產品的正確庫存
庫存 = 所有已完成入庫的實到數量總和 - 所有已出貨的銷售數量總和
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from database import DATABASE_URL
from models import Product

def recalculate_all_stock():
    """重新計算所有產品的正確庫存"""
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # 獲取所有產品
        products = db.query(Product).all()
        
        for product in products:
            # 計算入庫總量（已完成的入庫單）
            total_received = db.execute(text("""
                SELECT COALESCE(SUM(gri.received_quantity), 0) as total
                FROM goods_receipt_items gri
                JOIN goods_receipts gr ON gri.goods_receipt_id = gr.id
                WHERE gri.product_id = :product_id 
                AND gr.status = 'COMPLETED'
            """), {"product_id": product.id}).fetchone()
            
            # 計算出貨總量（已出貨的銷售單）
            total_shipped = db.execute(text("""
                SELECT COALESCE(SUM(soi.quantity), 0) as total
                FROM sales_order_items soi
                JOIN sales_orders so ON soi.sales_order_id = so.id
                WHERE soi.product_id = :product_id 
                AND so.status = 'SHIPPED'
            """), {"product_id": product.id}).fetchone()
            
            # 計算正確的庫存
            received_qty = total_received[0] if total_received else 0
            shipped_qty = total_shipped[0] if total_shipped else 0
            correct_stock = max(0, received_qty - shipped_qty)
            
            # 更新產品庫存
            old_stock = product.stock
            product.stock = correct_stock
            
            print(f"Product: {product.productName}")
            print(f"  入庫總量: {received_qty}")
            print(f"  出貨總量: {shipped_qty}")
            print(f"  舊庫存: {old_stock}")
            print(f"  新庫存: {correct_stock}")
            print(f"  差異: {correct_stock - old_stock}")
            print("-" * 50)
        
        db.commit()
        print("✅ 所有產品庫存重新計算完成！")
        
    except Exception as e:
        print(f"❌ 重新計算庫存時發生錯誤: {e}")
        db.rollback()
    finally:
        db.close()

def get_stock_summary():
    """獲取庫存摘要報告"""
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # 獲取庫存摘要
        result = db.execute(text("""
            SELECT 
                p.productName,
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
            ORDER BY p.productName
        """)).fetchall()
        
        print("=" * 80)
        print("庫存摘要報告")
        print("=" * 80)
        print(f"{'產品名稱':<20} {'當前庫存':<10} {'入庫總量':<10} {'出貨總量':<10} {'計算庫存':<10} {'差異':<10}")
        print("-" * 80)
        
        total_diff = 0
        for row in result:
            product_name = row[0]
            current_stock = row[1]
            total_received = row[2]
            total_shipped = row[3]
            calculated_stock = row[4]
            diff = current_stock - calculated_stock
            total_diff += abs(diff)
            
            status = "✅" if diff == 0 else "❌"
            print(f"{product_name:<20} {current_stock:<10} {total_received:<10} {total_shipped:<10} {calculated_stock:<10} {diff:<10} {status}")
        
        print("-" * 80)
        print(f"總差異數量: {total_diff}")
        
        if total_diff == 0:
            print("✅ 所有產品庫存都是正確的！")
        else:
            print("❌ 發現庫存差異，建議執行重新計算")
        
    except Exception as e:
        print(f"❌ 獲取庫存摘要時發生錯誤: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("庫存管理工具")
    print("1. 查看庫存摘要")
    print("2. 重新計算所有庫存")
    
    choice = input("請選擇操作 (1 或 2): ").strip()
    
    if choice == "1":
        get_stock_summary()
    elif choice == "2":
        print("⚠️  這將重新計算所有產品的庫存，確定要繼續嗎？")
        confirm = input("輸入 'yes' 確認: ").strip().lower()
        if confirm == "yes":
            recalculate_all_stock()
        else:
            print("操作已取消")
    else:
        print("無效的選擇")
