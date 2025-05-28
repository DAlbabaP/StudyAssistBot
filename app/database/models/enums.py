"""
Перечисления для моделей базы данных
"""
from enum import Enum


class OrderStatus(str, Enum):
    """Статусы заказов"""
    NEW = "new"                    # 🆕 Новый
    IN_PROGRESS = "in_progress"    # ⏳ В работе  
    READY = "ready"               # ✅ Готов
    WAITING_PAYMENT = "waiting_payment"  # 💰 Ждет оплаты
    SENT = "sent"                 # 📤 Отправлен
    CANCELLED = "cancelled"       # ❌ Отменен
    REVISION = "revision"         # 🔄 На доработке


class WorkType(str, Enum):
    """Типы учебных работ"""
    ESSAY = "essay"              # Реферат
    COURSEWORK = "coursework"    # Курсовая работа
    DIPLOMA = "diploma"          # Дипломная работа
    THESIS = "thesis"            # Диссертация
    REPORT = "report"            # Отчет
    PRESENTATION = "presentation" # Презентация
    OTHER = "other"              # Другое


# Emoji и описания для статусов
STATUS_EMOJI = {
    OrderStatus.NEW: "🆕",
    OrderStatus.IN_PROGRESS: "⏳",
    OrderStatus.READY: "✅",
    OrderStatus.WAITING_PAYMENT: "💰",
    OrderStatus.SENT: "📤",
    OrderStatus.CANCELLED: "❌",
    OrderStatus.REVISION: "🔄"
}

STATUS_NAMES = {
    OrderStatus.NEW: "Новый",
    OrderStatus.IN_PROGRESS: "В работе",
    OrderStatus.READY: "Готов",
    OrderStatus.WAITING_PAYMENT: "Ожидает оплаты",
    OrderStatus.SENT: "Отправлен",
    OrderStatus.CANCELLED: "Отменен",
    OrderStatus.REVISION: "На доработке"
}

WORK_TYPE_NAMES = {
    WorkType.ESSAY: "Реферат",
    WorkType.COURSEWORK: "Курсовая работа",
    WorkType.DIPLOMA: "Дипломная работа",
    WorkType.THESIS: "Диссертация",
    WorkType.REPORT: "Отчет",
    WorkType.PRESENTATION: "Презентация",
    WorkType.OTHER: "Другое"
}
