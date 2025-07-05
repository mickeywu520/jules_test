"""
測試號碼生成邏輯
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from database import DATABASE_URL

def test_number_generation():
    """測試號碼生成邏輯"""
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        today_str = "20250622"  # 使用固定日期進行測試
        
        print("=" * 60)
        print("號碼生成邏輯測試")
        print("=" * 60)
        
        # 測試採購單號
        print("\n1. 採購單號 (PO) 測試：")
        po_result = db.execute(text("""
            SELECT po_number 
            FROM purchase_orders 
            WHERE po_number LIKE :pattern 
            ORDER BY po_number DESC
        """), {"pattern": f"PO-{today_str}-%"}).fetchall()
        
        print(f"   當天已有的採購單號:")
        for row in po_result:
            print(f"   - {row[0]}")
        
        if po_result:
            last_po = po_result[0][0]
            last_number = int(last_po.split('-')[-1])
            next_number = last_number + 1
            next_po = f"PO-{today_str}-{next_number:03d}"
            print(f"   下一個採購單號應該是: {next_po}")
        else:
            print(f"   下一個採購單號應該是: PO-{today_str}-001")
        
        # 測試入庫單號
        print("\n2. 入庫單號 (GR) 測試：")
        gr_result = db.execute(text("""
            SELECT gr_number 
            FROM goods_receipts 
            WHERE gr_number LIKE :pattern 
            ORDER BY gr_number DESC
        """), {"pattern": f"GR-{today_str}-%"}).fetchall()
        
        print(f"   當天已有的入庫單號:")
        for row in gr_result:
            print(f"   - {row[0]}")
        
        if gr_result:
            last_gr = gr_result[0][0]
            last_number = int(last_gr.split('-')[-1])
            next_number = last_number + 1
            next_gr = f"GR-{today_str}-{next_number:03d}"
            print(f"   下一個入庫單號應該是: {next_gr}")
        else:
            print(f"   下一個入庫單號應該是: GR-{today_str}-001")
        
        # 測試銷售單號
        print("\n3. 銷售單號 (SO) 測試：")
        so_result = db.execute(text("""
            SELECT so_number 
            FROM sales_orders 
            WHERE so_number LIKE :pattern 
            ORDER BY so_number DESC
        """), {"pattern": f"SO-{today_str}-%"}).fetchall()
        
        print(f"   當天已有的銷售單號:")
        for row in so_result:
            print(f"   - {row[0]}")
        
        if so_result:
            last_so = so_result[0][0]
            last_number = int(last_so.split('-')[-1])
            next_number = last_number + 1
            next_so = f"SO-{today_str}-{next_number:03d}"
            print(f"   下一個銷售單號應該是: {next_so}")
        else:
            print(f"   下一個銷售單號應該是: SO-{today_str}-001")
        
        print("\n" + "=" * 60)
        print("測試完成")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 測試時發生錯誤: {e}")
    finally:
        db.close()

def check_duplicate_numbers():
    """檢查是否有重複的號碼"""
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("重複號碼檢查")
        print("=" * 60)
        
        # 檢查重複的採購單號
        print("\n1. 檢查重複的採購單號：")
        po_duplicates = db.execute(text("""
            SELECT po_number, COUNT(*) as count
            FROM purchase_orders
            GROUP BY po_number
            HAVING COUNT(*) > 1
        """)).fetchall()
        
        if po_duplicates:
            print("   發現重複的採購單號:")
            for row in po_duplicates:
                print(f"   - {row[0]} (重複 {row[1]} 次)")
        else:
            print("   ✅ 沒有重複的採購單號")
        
        # 檢查重複的入庫單號
        print("\n2. 檢查重複的入庫單號：")
        gr_duplicates = db.execute(text("""
            SELECT gr_number, COUNT(*) as count
            FROM goods_receipts
            GROUP BY gr_number
            HAVING COUNT(*) > 1
        """)).fetchall()
        
        if gr_duplicates:
            print("   發現重複的入庫單號:")
            for row in gr_duplicates:
                print(f"   - {row[0]} (重複 {row[1]} 次)")
        else:
            print("   ✅ 沒有重複的入庫單號")
        
        # 檢查重複的銷售單號
        print("\n3. 檢查重複的銷售單號：")
        so_duplicates = db.execute(text("""
            SELECT so_number, COUNT(*) as count
            FROM sales_orders
            GROUP BY so_number
            HAVING COUNT(*) > 1
        """)).fetchall()
        
        if so_duplicates:
            print("   發現重複的銷售單號:")
            for row in so_duplicates:
                print(f"   - {row[0]} (重複 {row[1]} 次)")
        else:
            print("   ✅ 沒有重複的銷售單號")
        
        print("\n" + "=" * 60)
        print("檢查完成")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 檢查時發生錯誤: {e}")
    finally:
        db.close()

def show_all_numbers():
    """顯示所有已生成的號碼"""
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print("所有已生成的號碼")
        print("=" * 80)
        
        # 顯示所有採購單號
        print("\n1. 採購單號:")
        po_numbers = db.execute(text("""
            SELECT po_number, purchase_date, status
            FROM purchase_orders
            ORDER BY po_number DESC
            LIMIT 10
        """)).fetchall()
        
        if po_numbers:
            print(f"   {'單號':<20} {'日期':<12} {'狀態':<15}")
            print("   " + "-" * 50)
            for row in po_numbers:
                print(f"   {row[0]:<20} {row[1]:<12} {row[2]:<15}")
        else:
            print("   沒有採購單")
        
        # 顯示所有入庫單號
        print("\n2. 入庫單號:")
        gr_numbers = db.execute(text("""
            SELECT gr_number, receipt_date, status
            FROM goods_receipts
            ORDER BY gr_number DESC
            LIMIT 10
        """)).fetchall()
        
        if gr_numbers:
            print(f"   {'單號':<20} {'日期':<12} {'狀態':<15}")
            print("   " + "-" * 50)
            for row in gr_numbers:
                print(f"   {row[0]:<20} {row[1]:<12} {row[2]:<15}")
        else:
            print("   沒有入庫單")
        
        # 顯示所有銷售單號
        print("\n3. 銷售單號:")
        so_numbers = db.execute(text("""
            SELECT so_number, sales_date, status
            FROM sales_orders
            ORDER BY so_number DESC
            LIMIT 10
        """)).fetchall()
        
        if so_numbers:
            print(f"   {'單號':<20} {'日期':<12} {'狀態':<15}")
            print("   " + "-" * 50)
            for row in so_numbers:
                print(f"   {row[0]:<20} {row[1]:<12} {row[2]:<15}")
        else:
            print("   沒有銷售單")
        
        print("\n" + "=" * 80)
        
    except Exception as e:
        print(f"❌ 顯示時發生錯誤: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("號碼生成測試工具")
    print("1. 測試號碼生成邏輯")
    print("2. 檢查重複號碼")
    print("3. 顯示所有號碼")
    
    choice = input("請選擇操作 (1, 2 或 3): ").strip()
    
    if choice == "1":
        test_number_generation()
    elif choice == "2":
        check_duplicate_numbers()
    elif choice == "3":
        show_all_numbers()
    else:
        print("無效的選擇")
