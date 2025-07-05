"""
添加 stock 欄位到 products 表的遷移腳本
"""
from sqlalchemy import create_engine, text
from database import DATABASE_URL

def add_stock_column():
    """添加 stock 欄位到 products 表"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as connection:
        try:
            # 檢查 stock 欄位是否已存在
            result = connection.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'products' AND column_name = 'stock'
            """))
            
            if result.fetchone() is None:
                # 添加 stock 欄位，預設值為 0
                connection.execute(text("""
                    ALTER TABLE products 
                    ADD COLUMN stock INTEGER DEFAULT 0 NOT NULL
                """))
                connection.commit()
                print("✅ Successfully added 'stock' column to products table")
            else:
                print("ℹ️ 'stock' column already exists in products table")
                
        except Exception as e:
            print(f"❌ Error adding stock column: {e}")
            connection.rollback()

if __name__ == "__main__":
    add_stock_column()
