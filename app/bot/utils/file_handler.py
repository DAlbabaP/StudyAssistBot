import os
import uuid
from pathlib import Path
from aiogram.types import File as TelegramFile
from aiogram import Bot
from app.config import settings


async def save_file(telegram_file: TelegramFile, order_id: int, bot: Bot) -> tuple[str, str]:
    """
    Сохранить файл от пользователя
    
    Args:
        telegram_file: Объект File от Telegram
        order_id: ID заказа
        bot: Экземпляр бота для скачивания
        
    Returns:
        tuple: (оригинальное имя файла, путь к сохраненному файлу)
    """
    try:
        # Создаем папку для заказа если её нет
        order_dir = Path(settings.upload_path) / str(order_id)
        order_dir.mkdir(parents=True, exist_ok=True)
        
        # Получаем оригинальное имя файла из пути Telegram
        original_filename = "unknown_file"
        if telegram_file.file_path:
            original_filename = os.path.basename(telegram_file.file_path)
        
        # Если имя файла пустое, генерируем его
        if not original_filename or original_filename == "unknown_file":
            file_extension = ".bin"
            if telegram_file.file_path and "." in telegram_file.file_path:
                file_extension = "." + telegram_file.file_path.split(".")[-1]
            original_filename = f"file_{uuid.uuid4().hex[:8]}{file_extension}"
        
        # 🔥 НОВОЕ: Добавляем префикс с номером заказа к имени файла
        prefixed_filename = f"order{order_id}_{original_filename}"
        file_path = order_dir / prefixed_filename
        
        # Правильное скачивание файла через bot
        await bot.download_file(telegram_file.file_path, file_path)
        
        # Возвращаем оригинальное имя для отображения в БД, но файл сохранен с префиксом
        return original_filename, str(file_path)
        
    except Exception as e:
        print(f"❌ Ошибка сохранения файла: {e}")
        raise


def format_file_size(size_bytes: int) -> str:
    """Форматировать размер файла"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def is_allowed_file_type(filename: str) -> bool:
    """Проверить, разрешен ли тип файла"""
    if not filename:
        return True  # Разрешаем файлы без имени
        
    allowed_extensions = {
        '.pdf', '.doc', '.docx', '.txt', '.rtf',  # Документы
        '.jpg', '.jpeg', '.png', '.gif', '.bmp',  # Изображения
        '.zip', '.rar', '.7z',  # Архивы
        '.xls', '.xlsx', '.csv',  # Таблицы
        '.ppt', '.pptx'  # Презентации
    }
    
    file_extension = Path(filename).suffix.lower()
    return file_extension in allowed_extensions or file_extension == ""


def get_file_type_emoji(filename: str) -> str:
    """Получить эмодзи для типа файла"""
    if not filename:
        return '📎'
        
    extension = Path(filename).suffix.lower()
    
    emoji_map = {
        '.pdf': '📄',
        '.doc': '📝', '.docx': '📝', '.txt': '📝', '.rtf': '📝',
        '.jpg': '🖼️', '.jpeg': '🖼️', '.png': '🖼️', '.gif': '🖼️', '.bmp': '🖼️',
        '.zip': '📦', '.rar': '📦', '.7z': '📦',
        '.xls': '📊', '.xlsx': '📊', '.csv': '📊',
        '.ppt': '📑', '.pptx': '📑'
    }
    
    return emoji_map.get(extension, '📎')