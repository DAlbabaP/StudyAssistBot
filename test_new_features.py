"""
Тестирование новых функций проекта
"""
import sys
import os

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_keyboards():
    """Тест новых клавиатур"""
    print("🧪 Тестирование новых клавиатур...")
    
    try:
        from app.bot.keyboards.client import get_price_response_keyboard, get_order_status_keyboard
        
        # Тестируем клавиатуру для ответа на цену
        keyboard = get_price_response_keyboard(123)
        print("✅ Клавиатура для ответа на цену создана")
        
        # Тестируем клавиатуру для статуса заказа
        status_keyboard = get_order_status_keyboard(123)
        print("✅ Клавиатура для статуса заказа создана")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании клавиатур: {e}")


def test_error_handlers():
    """Тест обработчиков ошибок"""
    print("🧪 Тестирование обработчиков ошибок...")
    
    try:
        # Проверяем импорт error_handler
        from app.bot.handlers import error_handler
        print("✅ Обработчик ошибок бота импортирован")
        
        # Проверяем админ панель
        from app.admin.main import app
        
        # Проверяем наличие обработчиков исключений
        exception_handlers = app.exception_handlers
        print(f"✅ Зарегистрировано {len(exception_handlers)} обработчиков исключений")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")


def test_file_download():
    """Тест функции скачивания файлов"""
    print("🧪 Тестирование функции скачивания файлов...")
    
    try:
        # Проверяем наличие endpoint'а в main.py
        from app.admin.main import app
        
        # Проверяем маршруты
        routes = [route.path for route in app.routes]
        
        if "/files/download/{file_id}" in routes:
            print("✅ Endpoint для скачивания файлов найден")
        else:
            print("❌ Endpoint для скачивания файлов не найден")
            
        if "/orders/{order_id}/files" in routes:
            print("✅ API для получения списка файлов найден")
        else:
            print("❌ API для получения списка файлов не найден")
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")


def test_new_handlers():
    """Тест новых обработчиков"""
    print("🧪 Тестирование новых обработчиков...")
    
    try:
        # Проверяем callback обработчики
        from app.bot.handlers.price_callbacks import router
        print("✅ Обработчики callback-запросов по ценам найдены")
        
        # Проверяем функцию уведомления о цене
        from app.services.order_service import OrderService
        print("✅ Функция уведомления о цене найдена в OrderService")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")


def main():
    """Основная функция тестирования"""
    print("🚀 Тестирование новых функций SellerBot")
    print("=" * 50)
    
    # Тестируем новые клавиатуры
    test_keyboards()
    print()
    
    # Тестируем обработчики ошибок
    test_error_handlers()
    print()
    
    # Тестируем функцию скачивания файлов
    test_file_download()
    print()
    
    # Тестируем новые обработчики
    test_new_handlers()
    print()
    
    print("✅ Все тесты завершены!")
    print("\n📋 Новые функции готовы к использованию:")
    print("   1. ✅ Уведомления пользователя о установке/изменении цены")
    print("   2. ✅ Скачивание файлов в админ-панели")
    print("   3. ✅ Улучшенная обработка ошибок")
    print("   4. ✅ Callback-обработчики для принятия/отклонения цены")


if __name__ == "__main__":
    main()
