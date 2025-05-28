import os
import uuid
from pathlib import Path
from aiogram.types import File as TelegramFile, Document
from aiogram import Bot
from app.config import settings


async def save_file(document: Document, order_id: int, bot: Bot) -> tuple[str, str]:
    """
    Сохранить файл от пользователя
    
    Args:
        document: Объект Document от Telegram
        order_id: ID заказа
        bot: Экземпляр бота для скачивания
        
    Returns:
        tuple: (оригинальное имя файла, путь к сохраненному файлу)
    """
    try:
        # Создаем папку для заказа если её нет
        order_dir = Path(settings.upload_path) / str(order_id)
        order_dir.mkdir(parents=True, exist_ok=True)
        
        # 🔥 ИСПРАВЛЕНО: Получаем оригинальное имя файла из Document
        original_filename = document.file_name
        
        # Если имя файла пустое или None, генерируем его
        if not original_filename or original_filename.strip() == "":
            # Пытаемся определить расширение по mime_type
            file_extension = ".bin"
            if document.mime_type:
                mime_extensions = {
                    'application/pdf': '.pdf',
                    'application/msword': '.doc',
                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
                    'text/plain': '.txt',
                    'image/jpeg': '.jpg',
                    'image/png': '.png',
                    'application/zip': '.zip',
                    'application/x-rar-compressed': '.rar'
                }
                file_extension = mime_extensions.get(document.mime_type, '.bin')
            
            original_filename = f"file_{uuid.uuid4().hex[:8]}{file_extension}"
        
        # 🔥 ИСПРАВЛЕНО: Сохраняем файл с ОРИГИНАЛЬНЫМ именем (без префиксов)
        # Но чтобы избежать конфликтов, сохраняем в папке заказа
        file_path = order_dir / original_filename
        
        # Если файл с таким именем уже существует, добавляем номер
        counter = 1
        base_name = Path(original_filename).stem
        extension = Path(original_filename).suffix
        
        while file_path.exists():
            new_filename = f"{base_name}_{counter}{extension}"
            file_path = order_dir / new_filename
            counter += 1
        
        # Получаем файл от Telegram и скачиваем его
        telegram_file = await bot.get_file(document.file_id)
        await bot.download_file(telegram_file.file_path, file_path)
        
        # Возвращаем имя сохраненного файла и путь
        final_filename = file_path.name
        
        print(f"✅ Файл сохранен: {original_filename} -> {final_filename}")
        print(f"   Путь: {file_path}")
        print(f"   Размер: {document.file_size} байт")
        
        return final_filename, str(file_path)
        
    except Exception as e:
        print(f"❌ Ошибка сохранения файла {original_filename}: {e}")
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