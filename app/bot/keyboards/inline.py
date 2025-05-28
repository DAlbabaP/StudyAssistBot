from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.database.models import OrderStatus, get_status_emoji, get_status_text
from typing import List


def get_order_details_keyboard(order_id: int, is_admin: bool = False) -> InlineKeyboardMarkup:
    """Клавиатура для детального просмотра заказа"""
    builder = InlineKeyboardBuilder()
    
    if is_admin:
        builder.add(InlineKeyboardButton(
            text="💰 Установить цену", 
            callback_data=f"set_price:{order_id}"
        ))
        builder.add(InlineKeyboardButton(
            text="🔄 Изменить статус", 
            callback_data=f"change_status:{order_id}"
        ))
        builder.add(InlineKeyboardButton(
            text="📎 Отправить файл", 
            callback_data=f"send_file:{order_id}"
        ))
        builder.adjust(1)
    
    builder.add(InlineKeyboardButton(
        text="🔙 Назад к списку", 
        callback_data="back_to_orders"
    ))
    
    return builder.as_markup()


def get_orders_pagination_keyboard(page: int, total_pages: int, user_id: int = None) -> InlineKeyboardMarkup:
    """Клавиатура пагинации заказов"""
    builder = InlineKeyboardBuilder()
    
    # Кнопки навигации
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(
            text="◀️ Назад", 
            callback_data=f"orders_page:{page-1}:{user_id or 'all'}"
        ))
    
    nav_buttons.append(InlineKeyboardButton(
        text=f"{page}/{total_pages}",
        callback_data="current_page"
    ))
    
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(
            text="Вперед ▶️", 
            callback_data=f"orders_page:{page+1}:{user_id or 'all'}"
        ))
    
    if nav_buttons:
        builder.row(*nav_buttons)
    
    return builder.as_markup()


def get_status_change_keyboard(order_id: int) -> InlineKeyboardMarkup:
    """Клавиатура изменения статуса заказа"""
    builder = InlineKeyboardBuilder()
    
    statuses = [
        (OrderStatus.NEW, "🆕 Новый"),
        (OrderStatus.IN_PROGRESS, "⏳ В работе"),
        (OrderStatus.READY, "✅ Готов"),
        (OrderStatus.WAITING_PAYMENT, "💰 Ждет оплаты"),
        (OrderStatus.SENT, "📤 Отправлен"),
        (OrderStatus.CANCELLED, "❌ Отменен")
    ]
    
    for status, text in statuses:
        builder.add(InlineKeyboardButton(
            text=text,
            callback_data=f"status:{order_id}:{status.value}"
        ))
    
    builder.add(InlineKeyboardButton(
        text="🔙 Назад",
        callback_data=f"order_details:{order_id}"
    ))
    
    builder.adjust(2)
    return builder.as_markup()


def get_admin_main_keyboard() -> InlineKeyboardMarkup:
    """Главная клавиатура админа"""
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(text="📋 Все заказы", callback_data="admin_orders:all"))
    builder.add(InlineKeyboardButton(text="🆕 Новые заказы", callback_data="admin_orders:new"))
    builder.add(InlineKeyboardButton(text="⏳ В работе", callback_data="admin_orders:in_progress"))
    builder.add(InlineKeyboardButton(text="✅ Готовые", callback_data="admin_orders:ready"))
    builder.add(InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats"))
    builder.add(InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast"))
    
    builder.adjust(2)
    return builder.as_markup()


def get_order_action_keyboard(order_id: int) -> InlineKeyboardMarkup:
    """Клавиатура действий с заказом для клиента"""
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(
        text="👁️ Подробнее",
        callback_data=f"order_details:{order_id}"
    ))
    
    return builder.as_markup()
