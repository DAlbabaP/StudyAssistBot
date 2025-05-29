from sqlalchemy.ext.declarative import declarative_base
# Добавьте импорт новой модели


# Базовый класс для всех моделей
Base = declarative_base()

# Импорт перечислений
from .enums import OrderStatus, WorkType, STATUS_EMOJI, STATUS_NAMES, WORK_TYPE_NAMES

# Импорт всех моделей для алембика
from .user import User
from .order import Order
from .file import OrderFile
from .status_history import StatusHistory
from .message import OrderMessage
from .payment import OrderPayment

def get_status_emoji(status: OrderStatus) -> str:
    """Получить эмодзи для статуса"""
    return STATUS_EMOJI.get(status, "❓")


def get_status_text(status: OrderStatus) -> str:
    """Получить текстовое описание статуса"""
    return STATUS_NAMES.get(status, "Неизвестный статус")


def get_work_type_text(work_type: WorkType) -> str:
    """Получить текстовое описание типа работы"""
    return WORK_TYPE_NAMES.get(work_type, "Неизвестный тип")
