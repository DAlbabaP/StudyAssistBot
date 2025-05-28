#!/usr/bin/env python3
"""
Скрипт миграции базы данных для добавления новых функций общения
"""

import os
import sys
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, text
from app.config import settings
from app.database.connection import engine


def migrate_database():
    """Выполнить миграцию базы данных"""
    print("🔄 Начинаем миграцию базы данных...")
    
    try:
        with engine.connect() as connection:
            # Начинаем транзакцию
            with connection.begin():
                
                # 1. Добавляем новые поля в таблицу order_files
                print("📁 Обновляем таблицу order_files...")
                
                # Проверяем, существует ли уже поле uploaded_by_admin
                result = connection.execute(text(
                    "PRAGMA table_info(order_files)"
                ))
                columns = [row[1] for row in result.fetchall()]
                
                if 'uploaded_by_admin' not in columns:
                    connection.execute(text(
                        "ALTER TABLE order_files ADD COLUMN uploaded_by_admin BOOLEAN DEFAULT 0 NOT NULL"
                    ))
                    print("  ✅ Добавлено поле uploaded_by_admin")
                
                if 'sent_to_user' not in columns:
                    connection.execute(text(
                        "ALTER TABLE order_files ADD COLUMN sent_to_user BOOLEAN DEFAULT 0 NOT NULL"
                    ))
                    print("  ✅ Добавлено поле sent_to_user")
                
                if 'sent_at' not in columns:
                    connection.execute(text(
                        "ALTER TABLE order_files ADD COLUMN sent_at DATETIME"
                    ))
                    print("  ✅ Добавлено поле sent_at")
                
                # 2. Создаем таблицу order_messages
                print("💬 Создаем таблицу order_messages...")
                
                connection.execute(text("""
                    CREATE TABLE IF NOT EXISTS order_messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        order_id INTEGER NOT NULL,
                        message_text TEXT NOT NULL,
                        from_admin BOOLEAN DEFAULT 0 NOT NULL,
                        sent_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                        delivered BOOLEAN DEFAULT 0 NOT NULL,
                        telegram_message_id INTEGER,
                        FOREIGN KEY (order_id) REFERENCES orders (id)
                    )
                """))
                print("  ✅ Таблица order_messages создана")
                
                # 3. Создаем индексы для оптимизации
                print("🔍 Создаем индексы...")
                
                connection.execute(text(
                    "CREATE INDEX IF NOT EXISTS idx_order_messages_order_id ON order_messages (order_id)"
                ))
                
                connection.execute(text(
                    "CREATE INDEX IF NOT EXISTS idx_order_messages_sent_at ON order_messages (sent_at)"
                ))
                
                connection.execute(text(
                    "CREATE INDEX IF NOT EXISTS idx_order_files_uploaded_by_admin ON order_files (uploaded_by_admin)"
                ))
                
                print("  ✅ Индексы созданы")
        
        print("✅ Миграция завершена успешно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка миграции: {e}")
        return False


def verify_migration():
    """Проверить результат миграции"""
    print("\n🔍 Проверяем результат миграции...")
    
    try:
        with engine.connect() as connection:
            # Проверяем структуру order_files
            result = connection.execute(text("PRAGMA table_info(order_files)"))
            order_files_columns = [row[1] for row in result.fetchall()]
            
            required_columns = ['uploaded_by_admin', 'sent_to_user', 'sent_at']
            for column in required_columns:
                if column in order_files_columns:
                    print(f"  ✅ order_files.{column}")
                else:
                    print(f"  ❌ order_files.{column} - НЕ НАЙДЕНО")
                    return False
            
            # Проверяем существование order_messages
            result = connection.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='order_messages'"
            ))
            
            if result.fetchone():
                print("  ✅ Таблица order_messages существует")
                
                # Проверяем структуру order_messages
                result = connection.execute(text("PRAGMA table_info(order_messages)"))
                message_columns = [row[1] for row in result.fetchall()]
                
                required_msg_columns = ['id', 'order_id', 'message_text', 'from_admin', 'sent_at', 'delivered']
                for column in required_msg_columns:
                    if column in message_columns:
                        print(f"    ✅ order_messages.{column}")
                    else:
                        print(f"    ❌ order_messages.{column} - НЕ НАЙДЕНО")
                        return False
            else:
                print("  ❌ Таблица order_messages НЕ НАЙДЕНА")
                return False
        
        print("\n🎉 Все проверки пройдены!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки: {e}")
        return False


def main():
    """Главная функция"""
    print("🗄️ Миграция базы данных для функций общения")
    print("=" * 50)
    
    # Проверяем подключение к БД
    if not os.path.exists("seller_bot.db"):
        print("❌ База данных seller_bot.db не найдена!")
        print("💡 Сначала запустите: python init_db.py")
        return False
    
    # Выполняем миграцию
    if migrate_database():
        # Проверяем результат
        if verify_migration():
            print("\n🚀 Миграция завершена успешно!")
            print("\n📝 Что добавлено:")
            print("1. ✅ Поля в order_files для файлов от админа")
            print("2. ✅ Таблица order_messages для истории общения")
            print("3. ✅ Индексы для оптимизации запросов")
            print("\n🎯 Теперь можно использовать новые функции!")
            return True
        else:
            print("\n❌ Миграция выполнена с ошибками")
            return False
    else:
        print("\n❌ Миграция не удалась")
        return False


if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)