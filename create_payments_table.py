"""
Создание таблицы платежей
"""
import sqlite3
import os

def create_payments_table():
    """Создать таблицу платежей"""
    db_path = "seller_bot.db"
    
    if not os.path.exists(db_path):
        print("❌ База данных не найдена!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Проверяем, существует ли таблица
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='order_payments'
        """)
        
        if cursor.fetchone():
            print("✅ Таблица order_payments уже существует")
            conn.close()
            return True
        
        # Создаем таблицу платежей
        cursor.execute("""
            CREATE TABLE order_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                payment_method VARCHAR(50),
                transaction_id VARCHAR(255),
                screenshot_file_id INTEGER,
                screenshot_message TEXT,
                is_verified BOOLEAN DEFAULT 0,
                is_rejected BOOLEAN DEFAULT 0,
                rejection_reason TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                verified_at DATETIME,
                rejected_at DATETIME,
                FOREIGN KEY (order_id) REFERENCES orders(id),
                FOREIGN KEY (screenshot_file_id) REFERENCES order_files(id)
            )
        """)
        
        conn.commit()
        conn.close()
        
        print("✅ Таблица order_payments создана успешно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка создания таблицы: {e}")
        return False

if __name__ == "__main__":
    create_payments_table()
