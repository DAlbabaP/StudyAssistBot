from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings

# Создание движка базы данных для SQLite (синхронный)
# Убираем async часть для синхронного подключения  
database_url = settings.database_url

engine = create_engine(
    database_url,
    echo=settings.debug,
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


def create_tables():
    """Создать все таблицы в базе данных"""
    from app.database.models import Base
    Base.metadata.create_all(bind=engine)
