# Создайте новый файл: app/bot/handlers/user_messages.py

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from app.services.user_service import UserService
from app.services.order_service import OrderService
from app.services.communication_service import CommunicationService
from app.database.connection import get_db_async
from app.database.models.enums import OrderStatus
from app.bot.keyboards.client import get_main_menu
from app.config import settings

router = Router()


@router.message(F.text & ~F.text.startswith('/') & ~F.text.in_([
    "📝 Новый заказ", "📋 Мои заказы", "ℹ️ О нас", "☎️ Поддержка",
    "❌ Отменить", "⏭️ Пропустить", "✅ Завершить загрузку", 
    "✅ Подтвердить заказ", "✏️ Редактировать", "🔙 Назад"
]))
async def handle_user_message(message: Message, state: FSMContext):
    """
    Обработчик обычных текстовых сообщений пользователя
    Сохраняет сообщения и привязывает к активному заказу
    """
    
    # Проверяем, не находится ли пользователь в процессе создания заказа
    current_state = await state.get_state()
    if current_state:
        # Если пользователь в процессе заполнения заказа, не обрабатываем как диалог
        return
    
    db = await get_db_async()
    try:
        user_service = UserService(db)
        order_service = OrderService(db)
        communication_service = CommunicationService(db)
        
        # Получаем пользователя
        user = user_service.get_user_by_telegram_id(message.from_user.id)
        if not user:
            await message.answer(
                "❌ Пользователь не найден. Нажмите /start для регистрации.",
                reply_markup=get_main_menu()
            )
            return
        
        # Ищем активный заказ пользователя (не завершенный и не отмененный)
        active_statuses = [
            OrderStatus.NEW, 
            OrderStatus.IN_PROGRESS, 
            OrderStatus.READY, 
            OrderStatus.WAITING_PAYMENT
        ]
        
        active_order = None
        user_orders = order_service.get_user_orders(user.id, page=1, per_page=10)
        
        for order in user_orders['orders']:
            if order.status in active_statuses:
                active_order = order
                break
        
        if not active_order:
            # Если нет активных заказов, отправляем в главное меню
            await message.answer(
                "💬 Ваше сообщение получено!\n\n"
                "У вас нет активных заказов для общения. "
                "Создайте новый заказ или выберите действие:",
                reply_markup=get_main_menu()
            )
            return
        
        # Сохраняем сообщение пользователя в БД
        user_message_saved = await communication_service.save_user_message(
            order_id=active_order.id,
            message_text=message.text,
            telegram_message_id=message.message_id
        )
        
        if user_message_saved:
            print(f"💬 Сообщение от пользователя {user.telegram_id} сохранено для заказа #{active_order.id}")
            
            # Отправляем подтверждение пользователю
            await message.answer(
                f"✅ <b>Сообщение получено!</b>\n\n"
                f"📋 <b>Заказ #{active_order.id}</b>\n"
                f"📝 {active_order.work_type}: {active_order.short_topic}\n\n"
                f"💬 Ваше сообщение передано администратору. "
                f"Ответ придет в этот чат.",
                parse_mode="HTML"
            )
            
            # Уведомляем администратора о новом сообщении
            await notify_admin_about_user_message(active_order, user, message.text)
        
        else:
            await message.answer(
                "❌ Ошибка сохранения сообщения. Попробуйте позже.",
                reply_markup=get_main_menu()
            )
    
    finally:
        db.close()


async def notify_admin_about_user_message(order, user, message_text: str):
    """Уведомить администратора о новом сообщении от пользователя"""
    try:
        from aiogram import Bot
        
        bot = Bot(token=settings.bot_token)
        
        # Формируем уведомление для админа
        admin_text = f"💬 <b>НОВОЕ СООБЩЕНИЕ ОТ КЛИЕНТА</b>\n\n"
        admin_text += f"📋 <b>Заказ #{order.id}</b>\n"
        admin_text += f"👤 <b>Клиент:</b> {user.full_name}"
        if user.username:
            admin_text += f" (@{user.username})"
        admin_text += f"\n📱 <b>Telegram ID:</b> {user.telegram_id}\n\n"
        
        admin_text += f"📝 <b>Тип работы:</b> {order.work_type}\n"
        admin_text += f"📋 <b>Тема:</b> {order.short_topic}\n\n"
        
        # Сообщение от пользователя
        preview = message_text[:200] + "..." if len(message_text) > 200 else message_text
        admin_text += f"💭 <b>Сообщение:</b>\n<i>'{preview}'</i>\n"        
        admin_text += f"🔗 <b>Ответить:</b> http://127.0.0.1:8000/orders/{order.id}\n"
        admin_text += f"💡 <b>Откройте заказ и нажмите 'Общение' для ответа</b>"
        
        # Отправляем уведомление админу
        await bot.send_message(
            chat_id=settings.admin_user_id,
            text=admin_text,
            parse_mode="HTML"
        )
        
        print(f"✅ Админ уведомлен о сообщении от {user.telegram_id} по заказу #{order.id}")
        
        # Закрываем сессию бота
        await bot.session.close()
        
    except Exception as e:
        print(f"❌ Ошибка уведомления админа о сообщении пользователя: {e}")


@router.message(F.text == "💬 Написать администратору")
async def write_to_admin_button(message: Message):
    """Обработчик кнопки 'Написать администратору'"""
    
    db = await get_db_async()
    try:
        user_service = UserService(db)
        order_service = OrderService(db)
        
        user = user_service.get_user_by_telegram_id(message.from_user.id)
        if not user:
            await message.answer("❌ Пользователь не найден. Нажмите /start")
            return
        
        # Получаем активные заказы
        user_orders = order_service.get_user_orders(user.id, page=1, per_page=5)
        
        active_orders = []
        for order in user_orders['orders']:
            if order.status in [OrderStatus.NEW, OrderStatus.IN_PROGRESS, OrderStatus.READY, OrderStatus.WAITING_PAYMENT]:
                active_orders.append(order)
        
        if not active_orders:
            await message.answer(
                "❌ У вас нет активных заказов для общения.\n\n"
                "Создайте новый заказ для начала общения с администратором.",
                reply_markup=get_main_menu()
            )
            return
        
        if len(active_orders) == 1:
            order = active_orders[0]
            text = f"💬 <b>Общение с администратором</b>\n\n"
            text += f"📋 <b>Заказ #{order.id}</b>\n"
            text += f"📝 {order.work_type}: {order.short_topic}\n\n"
            text += f"✍️ Просто напишите сообщение, и администратор его получит!"
        else:
            text = f"💬 <b>Общение с администратором</b>\n\n"
            text += f"У вас есть {len(active_orders)} активных заказов:\n\n"
            for order in active_orders[:3]:
                text += f"📋 #{order.id} - {order.work_type}\n"
            text += f"\n✍️ Ваше сообщение будет привязано к последнему активному заказу #{active_orders[0].id}"
        
        await message.answer(text, parse_mode="HTML")
    
    finally:
        db.close()