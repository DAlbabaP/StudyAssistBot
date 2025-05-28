"""
Основной файл для запуска админ-панели
"""
import uvicorn
import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.database.connection import create_tables
from app.admin.main import app as admin_app


async def startup_event():
    """Инициализация при запуске"""
    create_tables()
    logging.info("База данных инициализирована")


def create_app() -> FastAPI:
    """Создание FastAPI приложения"""
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Добавление обработчика запуска
    admin_app.add_event_handler("startup", startup_event)
    
    return admin_app


if __name__ == '__main__':
    try:
        # Запуск сервера с импортом в виде строки
        uvicorn.run(
            "app.admin.main:app",
            host=settings.admin_host,
            port=settings.admin_port,
            reload=settings.debug,
            log_level="info" if not settings.debug else "debug"
        )
    except KeyboardInterrupt:
        print("Сервер остановлен пользователем")
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        raise
