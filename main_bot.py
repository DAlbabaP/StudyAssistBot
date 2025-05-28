"""
Основной файл для запуска Telegram бота
"""
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.config import settings
from app.database.connection import create_tables
from app.bot.bot import create_bot
from app.bot.handlers import register_handlers


async def main():
    """Главная функция для запуска бота"""
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    try:
        # Инициализация базы данных
        create_tables()
        logger.info("База данных инициализирована")
        
        # Создание бота и диспетчера
        bot = Bot(
            token=settings.bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        
        dp = Dispatcher()
        
        # Регистрация обработчиков
        register_handlers(dp)
        logger.info("Обработчики зарегистрированы")
        
        # Запуск бота
        logger.info("Запуск бота...")
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        raise
    finally:
        logger.info("Бот остановлен")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен пользователем")
    except Exception as e:
        print(f"Критическая ошибка: {e}")
