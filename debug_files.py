#!/usr/bin/env python3
"""
Быстрый тест сохранения файлов
"""

import asyncio
import sys
import os
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import settings


async def test_file_saving():
    """Тест функции сохранения файлов"""
    print("🧪 Тестирование сохранения файлов")
    print("=" * 40)
    
    # Проверяем настройки
    print(f"📁 Upload path: {settings.upload_path}")
    
    # Создаем тестовую директорию
    upload_path = Path(settings.upload_path)
    test_order_dir = upload_path / "test_order"
    test_order_dir.mkdir(parents=True, exist_ok=True)
    
    # Создаем тестовый файл
    test_file = test_order_dir / "test_file.txt"
    with open(test_file, "w", encoding="utf-8") as f:
        f.write("Это тестовый файл для проверки сохранения")
    
    print(f"✅ Тестовый файл создан: {test_file}")
    print(f"✅ Размер: {test_file.stat().st_size} байт")
    print(f"✅ Существует: {test_file.exists()}")
    
    # Удаляем тестовый файл и директорию
    test_file.unlink()
    test_order_dir.rmdir()
    
    print("✅ Тест пройден - файловая система работает правильно")
    
    return True


async def main():
    """Главная функция"""
    try:
        success = await test_file_saving()
        
        if success:
            print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
            print("\n📝 Следующие шаги:")
            print("1. Замените файлы согласно инструкции")
            print("2. Перезапустите бота: python main_bot.py")
            print("3. Создайте новый заказ с файлами")
            print("4. Проверьте админ-панель")
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")


if __name__ == "__main__":
    asyncio.run(main())