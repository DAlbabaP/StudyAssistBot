from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings

# Создание движка базы данных для SQLite (синхронный)
# 🔥 ИСПРАВЛЕНО: Отключены SQL логи для чистоты консоли
database_url = settings.database_url

engine = create_engine(
    database_url,
    echo=False,  # 🔥 ИЗМЕНЕНО: было echo=settings.debug, теперь False
    # Для SQLite добавляем проверку foreign keys
    connect_args={"check_same_thread": False} if "sqlite" in database_url else {}
)

# Создание сессии
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Получить сессию базы данных"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_db_async():
    """Асинхронное получение сессии базы данных"""
    db = SessionLocal()
    return db


def get_db_session():
    """Получить сессию базы данных для прямого использования"""
    return SessionLocal()


def create_tables():
    """Создать все таблицы в базе данных"""
    from app.database.models import Base
    Base.metadata.create_all(bind=engine)