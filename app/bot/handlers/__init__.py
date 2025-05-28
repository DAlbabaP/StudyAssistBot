"""
Регистрация всех обработчиков бота
"""
from aiogram import Dispatcher

from app.bot.handlers import basic, orders, user_orders, admin, price_callbacks, error_handler
from app.bot.states.states import OrderStates, AdminStates


def register_handlers(dp: Dispatcher) -> None:
    """
    Регистрация всех обработчиков бота
    
    Args:
        dp: Диспетчер aiogram
    """
    # Регистрация обработчика ошибок (должен быть первым)
    dp.include_router(error_handler.router)
    
    # Регистрация базовых обработчиков
    dp.include_router(basic.router)
    
    # Регистрация обработчиков заказов
    dp.include_router(orders.router)
    
    # Регистрация обработчиков пользовательских заказов
    dp.include_router(user_orders.router)
    
    # Регистрация обработчиков callback-запросов по ценам
    dp.include_router(price_callbacks.router)
    
    # Регистрация админских обработчиков
    dp.include_router(admin.router)
    
    # Настройка обработки ошибок
    error_handler.setup_error_handling()
