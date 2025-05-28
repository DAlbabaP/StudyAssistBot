"""
Финальная проверка готовности проекта
"""

import os
import sys

def check_files():
    """Проверка наличия основных файлов"""
    required_files = [
        '.env.example',
        'requirements.txt', 
        'init_db.py',
        'main_bot.py',
        'main_admin.py',
        'start.py',
        'README.md'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Отсутствуют файлы: {', '.join(missing_files)}")
        return False
    
    print("✅ Все основные файлы на месте")
    return True

def check_modules():
    """Проверка загрузки основных модулей"""
    try:
        from app.config import settings
        print("✅ Конфигурация загружается")
    except Exception as e:
        print(f"❌ Ошибка загрузки конфигурации: {e}")
        return False
    
    try:
        from app.database.models import User, Order
        print("✅ Модели базы данных загружаются")
    except Exception as e:
        print(f"❌ Ошибка загрузки моделей: {e}")
        return False
    
    try:
        from app.bot.bot import create_bot
        print("✅ Модуль бота загружается")
    except Exception as e:
        print(f"❌ Ошибка загрузки бота: {e}")
        return False
    
    try:
        from app.admin.main import create_app
        print("✅ Модуль админ-панели загружается")
    except Exception as e:
        print(f"❌ Ошибка загрузки админ-панели: {e}")
        return False
    
    return True

def check_database():
    """Проверка базы данных"""
    if os.path.exists("seller_bot.db"):
        print("✅ База данных существует")
        return True
    else:
        print("⚠️  База данных не найдена (запустите init_db.py)")
        return True  # Это не критично

def check_uploads():
    """Проверка директории для файлов"""
    upload_dir = "uploads/files"
    if os.path.exists(upload_dir):
        print("✅ Директория для файлов существует")
    else:
        print("⚠️  Директория для файлов не найдена (создастся автоматически)")
    return True

def main():
    print("🔍 Проверка готовности проекта")
    print("=" * 40)
    
    all_ok = True
    
    all_ok &= check_files()
    all_ok &= check_modules()
    all_ok &= check_database()
    all_ok &= check_uploads()
    
    print("\n" + "=" * 40)
    
    if all_ok:
        print("🎉 Проект готов к запуску!")
        print("\n📝 Следующие шаги:")
        print("1. Настройте .env файл с вашими токенами")
        print("2. Запустите: python init_db.py (если БД не создана)")
        print("3. Запустите: python start.py")
        print("\n📖 Подробная инструкция в README.md")
    else:
        print("❌ Проект не готов к запуску")
        print("💡 Исправьте ошибки выше")

if __name__ == "__main__":
    main()
