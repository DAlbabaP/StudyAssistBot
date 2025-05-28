"""
Скрипт для инициализации базы данных SQLite
Запускать перед первым использованием бота
"""

import os
from app.database.connection import engine, create_tables

def init_database():
    """Инициализация базы данных"""
    print("🗄️ Инициализация базы данных...")
    
    # Создаем директорию для uploads, если её нет
    upload_dir = "uploads/files"
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
        print(f"📁 Создана директория: {upload_dir}")
    
    # Создаем таблицы
    try:
        create_tables()
        print("✅ База данных успешно инициализирована!")
        print("📋 Созданы таблицы:")
        print("   - users (пользователи)")
        print("   - orders (заказы)")
        print("   - order_files (файлы заказов)")
        print("   - status_history (история статусов)")
        
        # Проверяем, что файл базы данных создался
        if os.path.exists("seller_bot.db"):
            print("💾 Файл базы данных: seller_bot.db")
        
    except Exception as e:
        print(f"❌ Ошибка при инициализации базы данных: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = init_database()
    if success:
        print("\n🚀 Теперь можно запускать бота:")
        print("   python main_bot.py")
        print("\n🌐 Или админ-панель:")
        print("   python main_admin.py")
    else:
        print("\n❌ Не удалось инициализировать базу данных")
