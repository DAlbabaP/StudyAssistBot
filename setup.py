#!/usr/bin/env python3
"""
Скрипт инициализации проекта SellerBot
"""
import asyncio
import os
import sys
import subprocess
from pathlib import Path

def print_step(step_num: int, description: str):
    """Красивый вывод шагов"""
    print(f"\n{'='*60}")
    print(f"ШАГ {step_num}: {description}")
    print(f"{'='*60}")

def run_command(command: str, description: str = ""):
    """Выполнить команду в терминале"""
    if description:
        print(f"  → {description}")
    print(f"  $ {command}")
    
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"  ❌ Ошибка: {result.stderr}")
        return False
    
    if result.stdout:
        print(f"  ✅ {result.stdout.strip()}")
    
    return True

def check_requirements():
    """Проверка системных требований"""
    print_step(1, "ПРОВЕРКА СИСТЕМНЫХ ТРЕБОВАНИЙ")
    
    # Проверка Python
    python_version = sys.version_info
    if python_version.major != 3 or python_version.minor < 8:
        print("  ❌ Требуется Python 3.8 или выше")
        return False
    print(f"  ✅ Python {python_version.major}.{python_version.minor}")
    
    # Проверка pip
    if not run_command("pip --version", "Проверка pip"):
        return False
    
    return True

def install_dependencies():
    """Установка зависимостей"""
    print_step(2, "УСТАНОВКА ЗАВИСИМОСТЕЙ")
    
    if not run_command("pip install -r requirements.txt", "Установка Python пакетов"):
        return False
    
    return True

def setup_environment():
    """Настройка окружения"""
    print_step(3, "НАСТРОЙКА ОКРУЖЕНИЯ")
    
    # Проверка .env файла
    if not os.path.exists(".env"):
        print("  ⚠️  Файл .env не найден")
        if os.path.exists(".env.example"):
            print("  → Копирование .env.example в .env")
            import shutil
            shutil.copy(".env.example", ".env")
            print("  ✅ Файл .env создан")
            print("  📝 ВАЖНО: Отредактируйте файл .env с вашими настройками!")
        else:
            print("  ❌ Файл .env.example не найден")
            return False
    else:
        print("  ✅ Файл .env существует")
    
    # Создание директорий
    directories = [
        "uploads/files",
        "logs"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"  ✅ Директория {directory} создана")
    
    return True

def setup_database():
    """Настройка базы данных"""
    print_step(4, "НАСТРОЙКА БАЗЫ ДАННЫХ")
    
    print("  📋 Для работы с базой данных вам нужно:")
    print("     1. Установить PostgreSQL")
    print("     2. Создать базу данных 'seller_bot'")
    print("     3. Обновить DATABASE_URL в .env файле")
    
    # Попытка выполнить миграции
    print("  → Попытка применения миграций...")
    if run_command("alembic upgrade head", "Применение миграций"):
        print("  ✅ Миграции применены успешно")
    else:
        print("  ⚠️  Миграции не применены. Настройте базу данных вручную.")
    
    return True

def setup_telegram_bot():
    """Настройка Telegram бота"""
    print_step(5, "НАСТРОЙКА TELEGRAM БОТА")
    
    print("  📋 Для настройки Telegram бота:")
    print("     1. Создайте бота через @BotFather")
    print("     2. Получите токен бота")
    print("     3. Добавьте токен в BOT_TOKEN в .env файле")
    print("     4. Получите ваш Telegram ID через @userinfobot")
    print("     5. Добавьте ID в ADMIN_USER_ID в .env файле")
    
    return True

def final_instructions():
    """Финальные инструкции"""
    print_step(6, "ЗАВЕРШЕНИЕ УСТАНОВКИ")
    
    print("  🎉 Установка завершена!")
    print()
    print("  📝 СЛЕДУЮЩИЕ ШАГИ:")
    print("     1. Отредактируйте .env файл с вашими настройками")
    print("     2. Убедитесь, что PostgreSQL запущен")
    print("     3. Примените миграции: alembic upgrade head")
    print("     4. Запустите бота: python main_bot.py")
    print("     5. Запустите админ-панель: python main_admin.py")
    print()
    print("  🌐 Админ-панель будет доступна по адресу: http://localhost:8000")
    print()
    print("  📚 Больше информации в README.md")

def main():
    """Основная функция"""
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║                🤖 УСТАНОВКА SELLERBOT 🤖                     ║
    ║                                                              ║
    ║    Telegram бот для образовательных заказов с админ-панелью  ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    try:
        if not check_requirements():
            sys.exit(1)
        
        if not install_dependencies():
            sys.exit(1)
        
        if not setup_environment():
            sys.exit(1)
        
        if not setup_database():
            # Не выходим, так как БД может быть настроена позже
            pass
        
        if not setup_telegram_bot():
            # Не выходим, так как бот может быть настроен позже
            pass
        
        final_instructions()
        
    except KeyboardInterrupt:
        print("\n\n  ⚠️  Установка прервана пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n  ❌ Неожиданная ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
