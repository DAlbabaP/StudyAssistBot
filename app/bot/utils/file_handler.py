import os
import uuid
from pathlib import Path
from aiogram.types import Document, Message
from app.config import settings


async def save_file(document: Document, order_id: int) -> tuple[str, str]:
    """
    Сохранить файл от пользователя
    
    Args:
        document: Документ от пользователя
        order_id: ID заказа
        
    Returns:
        tuple: (имя файла, путь к файлу)
    """
    # Создаем папку для заказа если её нет
    order_dir = Path(settings.upload_path) / str(order_id)
    order_dir.mkdir(parents=True, exist_ok=True)
    
    # Генерируем уникальное имя файла
    file_extension = Path(document.file_name).suffix if document.file_name else ''
    unique_filename = f"{uuid.uuid4().hex}{file_extension}"
    file_path = order_dir / unique_filename
    
    # Сохраняем файл
    await document.download(destination=file_path)
    
    return document.file_name, str(file_path)


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
    allowed_extensions = {
        '.pdf', '.doc', '.docx', '.txt', '.rtf',  # Документы
        '.jpg', '.jpeg', '.png', '.gif', '.bmp',  # Изображения
        '.zip', '.rar', '.7z',  # Архивы
        '.xls', '.xlsx', '.csv',  # Таблицы
        '.ppt', '.pptx'  # Презентации
    }
    
    file_extension = Path(filename).suffix.lower()
    return file_extension in allowed_extensions


def get_file_type_emoji(filename: str) -> str:
    """Получить эмодзи для типа файла"""
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
