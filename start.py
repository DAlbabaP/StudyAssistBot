"""
Скрипт быстрого запуска для Telegram бота и админ-панели
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def check_requirements():
    """Проверка установки зависимостей"""
    try:
        import aiogram
        import fastapi
        import sqlalchemy
        print("✅ Все зависимости установлены")
        return True
    except ImportError as e:
        print(f"❌ Не установлены зависимости: {e}")
        print("💡 Запустите: pip install -r requirements.txt")
        return False

def check_env_file():
    """Проверка наличия .env файла"""
    if not os.path.exists(".env"):
        print("❌ Файл .env не найден")
        print("💡 Скопируйте .env.example в .env и заполните настройки")
        return False
    
    # Проверяем основные переменные
    with open(".env", "r", encoding="utf-8") as f:
        content = f.read()
        
    if "your_bot_token_here" in content:
        print("❌ Не заполнен BOT_TOKEN в .env файле")
        print("💡 Получите токен у @BotFather и замените в .env")
        return False
    
    if "your_telegram_user_id" in content:
        print("❌ Не заполнен ADMIN_USER_ID в .env файле")
        print("💡 Узнайте свой ID у @userinfobot и замените в .env")
        return False
    
    print("✅ Файл .env настроен")
    return True

def check_database():
    """Проверка наличия базы данных"""
    if not os.path.exists("seller_bot.db"):
        print("📋 База данных не найдена, инициализируем...")
        try:
            subprocess.run([sys.executable, "init_db.py"], check=True)
            return True
        except subprocess.CalledProcessError:
            print("❌ Ошибка инициализации базы данных")
            return False
    else:
        print("✅ База данных найдена")
        return True

def start_bot():
    """Запуск бота"""
    print("\n🤖 Запуск Telegram бота...")
    try:
        subprocess.Popen([sys.executable, "main_bot.py"])
        print("✅ Бот запущен успешно")
        return True
    except Exception as e:
        print(f"❌ Ошибка запуска бота: {e}")
        return False

def start_admin():
    """Запуск админ-панели"""
    print("\n🌐 Запуск админ-панели...")
    try:
        subprocess.Popen([sys.executable, "main_admin.py"])
        print("✅ Админ-панель запущена успешно")
        print("🔗 Откройте: http://127.0.0.1:8000")
        print("🔑 Пароль для входа: admin123")
        return True
    except Exception as e:
        print(f"❌ Ошибка запуска админ-панели: {e}")
        return False

def main():
    """Главная функция"""
    print("🚀 Запуск Telegram бота для образовательных заказов")
    print("=" * 50)
    
    # Проверки
    if not check_requirements():
        return
    
    if not check_env_file():
        return
    
    if not check_database():
        return
    
    print("\n" + "=" * 50)
    print("🎯 Выберите действие:")
    print("1. Запустить только бота")
    print("2. Запустить только админ-панель")
    print("3. Запустить бота и админ-панель")
    print("4. Выход")
    
    choice = input("\nВведите номер (1-4): ").strip()
    
    if choice == "1":
        start_bot()
    elif choice == "2":
        start_admin()
    elif choice == "3":
        start_bot()
        time.sleep(2)  # Небольшая задержка между запусками
        start_admin()
    elif choice == "4":
        print("👋 До свидания!")
        return
    else:
        print("❌ Неверный выбор")
        return
    
    print("\n" + "=" * 50)
    print("🏃‍♂️ Приложения запущены!")
    print("📝 Для остановки нажмите Ctrl+C в соответствующих окнах")
    print("📖 Документация: README.md")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Завершение работы...")
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")
        input("Нажмите Enter для выхода...")
