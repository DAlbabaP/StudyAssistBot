"""
Обработчики ошибок для бота
"""
import logging
from aiogram import Router
from aiogram.types import Update, ErrorEvent
from aiogram.exceptions import TelegramBadRequest, TelegramNotFound

router = Router()

# Настройка логгера
logger = logging.getLogger(__name__)


@router.error()
async def error_handler(event: ErrorEvent, update: Update):
    """
    Глобальный обработчик ошибок для бота
    """
    exception = event.exception
    
    # Логируем ошибку
    logger.error(f"Update {update} caused error {exception}", exc_info=True)
    
    # Обрабатываем разные типы ошибок
    if isinstance(exception, TelegramBadRequest):
        if "message is not modified" in str(exception):
            # Игнорируем ошибки при попытке изменить сообщение на то же самое
            return True
        elif "message to edit not found" in str(exception):
            # Игнорируем ошибки при попытке изменить несуществующее сообщение
            return True
        elif "can't parse entities" in str(exception):
            # Ошибки парсинга HTML/Markdown
            logger.warning(f"Parse error: {exception}")
            return True
    
    elif isinstance(exception, TelegramNotFound):
        # Пользователь заблокировал бота или удалил чат
        logger.warning(f"User not found or blocked bot: {exception}")
        return True
    
    # Для других ошибок возвращаем False, чтобы они обрабатывались стандартно
    return False


def setup_error_handling():
    """
    Настройка обработки ошибок
    """
    # Настройка логгирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('bot_errors.log'),
            logging.StreamHandler()
        ]
    )
    
    # Устанавливаем уровень логгирования для различных модулей
    logging.getLogger('aiogram').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
