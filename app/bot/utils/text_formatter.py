from app.database.models.order import Order
from app.database.models import OrderStatus, get_status_emoji, get_status_text
from datetime import datetime


def format_order_info(order: Order, detailed: bool = False) -> str:
    """Форматировать информацию о заказе"""
    status_emoji = get_status_emoji(order.status)
    status_text = get_status_text(order.status)
    
    # Базовая информация
    text = f"🆔 <b>Заказ #{order.id}</b>\n"
    text += f"📝 <b>Тип:</b> {order.work_type}\n"
    text += f"📚 <b>Предмет:</b> {order.subject}\n"
    
    if detailed:
        text += f"📋 <b>Тема:</b> {order.topic}\n"
        text += f"📏 <b>Объем:</b> {order.volume}\n"
        text += f"⏰ <b>Срок:</b> {order.deadline}\n"
        
        if order.requirements:
            requirements = order.requirements[:200] + "..." if len(order.requirements) > 200 else order.requirements
            text += f"📄 <b>Требования:</b> {requirements}\n"
        
        if order.files_count > 0:
            text += f"📎 <b>Файлов:</b> {order.files_count}\n"
        
        if order.price:
            text += f"💰 <b>Цена:</b> {order.price} руб.\n"
    else:
        # Краткая тема
        short_topic = order.topic[:50] + "..." if len(order.topic) > 50 else order.topic
        text += f"📋 <b>Тема:</b> {short_topic}\n"
    
    text += f"📊 <b>Статус:</b> {status_emoji} {status_text}\n"
    text += f"📅 <b>Создан:</b> {order.created_at.strftime('%d.%m.%Y %H:%M')}\n"
    
    return text


def format_order_list(orders: list, page: int, total_pages: int) -> str:
    """Форматировать список заказов"""
    if not orders:
        return "📭 <b>Заказов не найдено</b>"
    
    text = f"📋 <b>Ваши заказы</b> (стр. {page}/{total_pages}):\n\n"
    
    for order in orders:
        status_emoji = get_status_emoji(order.status)
        short_topic = order.topic[:30] + "..." if len(order.topic) > 30 else order.topic
        
        text += f"🆔 <b>#{order.id}</b> - {order.work_type}\n"
        text += f"📋 {short_topic}\n"
        text += f"📊 {status_emoji} {get_status_text(order.status)}\n"
        
        if order.price:
            text += f"💰 {order.price} руб.\n"
        
        text += f"📅 {order.created_at.strftime('%d.%m.%Y')}\n"
        text += "➖➖➖➖➖➖➖➖➖➖\n"
    
    return text


def format_order_summary(order_data: dict) -> str:
    """Форматировать сводку заказа для подтверждения"""
    text = "📋 <b>Сводка заказа:</b>\n\n"
    text += f"📝 <b>Тип работы:</b> {order_data['work_type']}\n"
    text += f"📚 <b>Предмет:</b> {order_data['subject']}\n"
    text += f"📋 <b>Тема:</b> {order_data['topic']}\n"
    text += f"📏 <b>Объем:</b> {order_data['volume']}\n"
    text += f"⏰ <b>Срок выполнения:</b> {order_data['deadline']}\n"
    
    if order_data.get('requirements'):
        text += f"📄 <b>Требования:</b> {order_data['requirements']}\n"
    
    if order_data.get('files'):
        text += f"📎 <b>Файлов прикреплено:</b> {len(order_data['files'])}\n"
    
    text += "\n✅ Проверьте данные и подтвердите заказ"
    
    return text


def format_admin_order_info(order: Order) -> str:
    """Форматировать информацию о заказе для админа"""
    text = format_order_info(order, detailed=True)
    
    # Добавляем информацию о клиенте
    text += f"\n👤 <b>Клиент:</b>\n"
    text += f"🆔 ID: {order.user.telegram_id}\n"
    text += f"👨‍💼 Имя: {order.user.full_name}\n"
    
    if order.user.username:
        text += f"📱 Username: @{order.user.username}\n"
    
    if order.user.phone:
        text += f"☎️ Телефон: {order.user.phone}\n"
    
    return text


def format_work_type(work_type: str) -> str:
    """Очистить тип работы от эмодзи"""
    emoji_map = {
        "📚 Реферат": "Реферат",
        "📄 Курсовая работа": "Курсовая работа",
        "🎓 Дипломная работа": "Дипломная работа",
        "📝 Эссе": "Эссе",
        "🧮 Контрольная работа": "Контрольная работа",
        "📊 Отчет по практике": "Отчет по практике",
        "🔬 Лабораторная работа": "Лабораторная работа",
        "📋 Другое": "Другое"
    }
    
    return emoji_map.get(work_type, work_type)
