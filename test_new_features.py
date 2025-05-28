#!/usr/bin/env python3
"""
Скрипт для тестирования новых функций SellerBot
"""

import os
import sys
import asyncio
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Тест импортов всех модулей"""
    print("🧪 Тестирование импортов...")
    
    try:
        # Тест основных модулей
        from app.config import settings
        print("✅ Настройки загружены")
        
        from app.database.models import User, Order, OrderFile
        print("✅ Модели БД импортированы")
        
        from app.services.order_service import OrderService
        print("✅ OrderService импортирован")
        
        from app.bot.handlers.orders import send_admin_notification
        print("✅ Функция уведомления админа импортирована")
        
        from app.bot.handlers.price_callbacks import router
        print("✅ Callback обработчики импортированы")
        
        from app.bot.keyboards.client import get_price_response_keyboard
        print("✅ Клавиатуры импортированы")
        
        return True
        
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False


def test_config():
    """Тест конфигурации"""
    print("\n🧪 Тестирование конфигурации...")
    
    try:
        from app.config import settings
        
        # Проверяем основные настройки
        if not settings.bot_token or settings.bot_token == "your_bot_token_here":
            print("❌ BOT_TOKEN не настроен в .env файле")
            return False
        else:
            print("✅ BOT_TOKEN настроен")
        
        if not settings.admin_user_id or settings.admin_user_id == 0:
            print("❌ ADMIN_USER_ID не настроен в .env файле")
            return False
        else:
            print(f"✅ ADMIN_USER_ID настроен: {settings.admin_user_id}")
        
        print(f"✅ Database URL: {settings.database_url}")
        print(f"✅ Upload path: {settings.upload_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка конфигурации: {e}")
        return False


def test_database():
    """Тест подключения к базе данных"""
    print("\n🧪 Тестирование базы данных...")
    
    try:
        from app.database.connection import get_db_async, create_tables
        
        # Создаем таблицы
        create_tables()
        print("✅ Таблицы созданы/обновлены")
        
        # Проверяем подключение
        async def check_db():
            db = await get_db_async()
            if db:
                db.close()
                return True
            return False
        
        result = asyncio.run(check_db())
        if result:
            print("✅ Подключение к БД работает")
            return True
        else:
            print("❌ Не удалось подключиться к БД")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка БД: {e}")
        return False


def test_directories():
    """Тест необходимых директорий"""
    print("\n🧪 Тестирование директорий...")
    
    try:
        from app.config import settings
        
        # Проверяем upload директорию
        upload_path = Path(settings.upload_path)
        if not upload_path.exists():
            upload_path.mkdir(parents=True, exist_ok=True)
            print(f"✅ Создана директория: {upload_path}")
        else:
            print(f"✅ Директория существует: {upload_path}")
        
        # Проверяем файлы шаблонов
        template_files = [
            "app/admin/templates/order_detail.html",
            "app/admin/templates/base.html",
        ]
        
        for template in template_files:
            if Path(template).exists():
                print(f"✅ Шаблон найден: {template}")
            else:
                print(f"❌ Шаблон не найден: {template}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка директорий: {e}")
        return False


def test_bot_token():
    """Тест валидности токена бота"""
    print("\n🧪 Тестирование токена бота...")
    
    try:
        from app.config import settings
        from aiogram import Bot
        
        if settings.bot_token == "your_bot_token_here":
            print("❌ Токен бота не настроен")
            return False
        
        async def check_token():
            try:
                bot = Bot(token=settings.bot_token)
                me = await bot.get_me()
                await bot.session.close()
                return me
            except Exception as e:
                print(f"❌ Ошибка токена: {e}")
                return None
        
        me = asyncio.run(check_token())
        if me:
            print(f"✅ Бот подключен: @{me.username} ({me.first_name})")
            return True
        else:
            print("❌ Не удалось подключиться к боту")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка тестирования бота: {e}")
        return False


def test_admin_endpoints():
    """Тест endpoints админ-панели"""
    print("\n🧪 Тестирование админ-панели...")
    
    try:
        from app.admin.main import app
        
        # Проверяем основные роуты
        routes = [route.path for route in app.routes]
        
        required_routes = [
            "/files/download/{file_id}",
            "/orders/{order_id}/files",
            "/orders/{order_id}/price",
            "/orders/{order_id}/status"
        ]
        
        for route in required_routes:
            if route in routes:
                print(f"✅ Роут найден: {route}")
            else:
                print(f"❌ Роут не найден: {route}")
                return False
        
        print("✅ Все необходимые роуты админ-панели найдены")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования админ-панели: {e}")
        return False


def main():
    """Главная функция тестирования"""
    print("🚀 Тестирование новых функций SellerBot")
    print("=" * 60)
    
    tests = [
        ("Импорты модулей", test_imports),
        ("Конфигурация", test_config),
        ("База данных", test_database),
        ("Директории", test_directories),
        ("Токен бота", test_bot_token),
        ("Админ-панель", test_admin_endpoints)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Критическая ошибка в тесте '{test_name}': {e}")
            results.append((test_name, False))
    
    # Итоговый отчет
    print("\n" + "=" * 60)
    print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ ПРОШЕЛ" if result else "❌ ПРОВАЛЕН"
        print(f"{test_name:.<40} {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("=" * 60)
    print(f"Всего тестов: {len(results)}")
    print(f"Прошло: {passed}")
    print(f"Провалено: {failed}")
    
    if failed == 0:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("Можно запускать бота и админ-панель")
        print("\nЗапуск:")
        print("  python main_bot.py")
        print("  python main_admin.py")
    else:
        print(f"\n⚠️  ОБНАРУЖЕНЫ ПРОБЛЕМЫ: {failed}")
        print("Исправьте ошибки перед запуском")
        print("\nПроверьте:")
        print("  1. Файл .env настроен корректно")
        print("  2. Все файлы заменены согласно инструкции")
        print("  3. Установлены все зависимости: pip install -r requirements.txt")


if __name__ == "__main__":
    main()