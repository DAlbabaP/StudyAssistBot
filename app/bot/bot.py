import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import settings
from app.bot.handlers import basic, orders, user_orders, admin, price_callbacks, user_messages
from app.database.connection import create_tables

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Глобальный экземпляр бота для использования в уведомлениях
bot = Bot(token=settings.bot_token)


def create_bot():
    """Создание экземпляра бота для тестирования"""
    bot = Bot(token=settings.bot_token)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
      # Регистрация роутеров
    dp.include_router(basic.router)
    dp.include_router(orders.router)
    dp.include_router(user_orders.router)
    dp.include_router(admin.router)
    dp.include_router(price_callbacks.router)
    dp.include_router(user_messages.router)
    
    return bot, dp


async def main():
    """Главная функция запуска бота"""
    
    # Создаем таблицы в базе данных
    try:
        create_tables()
        logger.info("База данных инициализирована")
    except Exception as e:
        logger.error(f"Ошибка инициализации базы данных: {e}")
        return
      # Инициализация бота и диспетчера
    bot = Bot(token=settings.bot_token)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
      # Регистрация роутеров
    dp.include_router(basic.router)
    dp.include_router(orders.router)
    dp.include_router(user_orders.router)
    dp.include_router(admin.router)
    dp.include_router(price_callbacks.router)
    dp.include_router(user_messages.router)
    
    # Запуск бота
    try:
        logger.info("Бот запущен")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
