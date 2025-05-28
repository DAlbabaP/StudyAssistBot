from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from app.bot.keyboards.client import get_main_menu, get_order_status_keyboard
from app.services.order_service import OrderService
from app.services.user_service import UserService
from app.database.connection import get_db_async
from app.database.models import OrderStatus, STATUS_EMOJI
from app.config import settings

router = Router()


@router.callback_query(F.data.startswith("accept_price:"))
async def accept_price_callback(callback: CallbackQuery, state: FSMContext):
    """Обработка принятия цены пользователем"""
    try:
        order_id = int(callback.data.split(":")[1])
        
        db = await get_db_async()
        try:
            order_service = OrderService(db)
            order = order_service.get_order_by_id(order_id)
            
            if not order:
                await callback.answer("❌ Заказ не найден", show_alert=True)
                return
            
            if order.user.telegram_id != callback.from_user.id:
                await callback.answer("❌ Это не ваш заказ", show_alert=True)
                return
            
            if not order.price:
                await callback.answer("❌ Цена не установлена", show_alert=True)
                return
            
            # Обновляем статус заказа на "ждет оплаты"
            success = order_service.update_order_status(order_id, OrderStatus.WAITING_PAYMENT)
            
            if success:
                # Сохраняем данные для уведомлений до закрытия сессии
                order_data = {
                    'id': order.id,
                    'price': order.price,
                    'work_type': order.work_type,
                    'topic': order.topic,
                    'user_first_name': order.user.first_name,
                    'user_last_name': order.user.last_name,
                    'user_username': order.user.username
                }
                
                # Отправляем уведомление пользователю
                await callback.message.edit_text(
                    f"✅ <b>Вы приняли цену {order_data['price']} ₽</b>\n\n"
                    f"📋 <b>Заказ #{order_data['id']}</b>\n"
                    f"📝 {order_data['work_type']}: {order_data['topic'][:50]}...\n\n"
                    f"💰 Статус изменен на: <b>Ожидает оплаты</b>\n\n"
                    f"📞 Для оплаты свяжитесь с нами через поддержку.",
                    parse_mode="HTML",
                    reply_markup=get_order_status_keyboard(order_id)
                )

                # Уведомляем админа о принятии цены
                await send_admin_notification_accept(order_data)
                
                await callback.answer("✅ Цена принята!")
            else:
                await callback.answer("❌ Ошибка обновления статуса", show_alert=True)
        finally:
            db.close()
                
    except Exception as e:
        print(f"Ошибка при принятии цены: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)


@router.callback_query(F.data.startswith("decline_price:"))
async def decline_price_callback(callback: CallbackQuery, state: FSMContext):
    """Обработка отклонения цены пользователем"""
    try:
        order_id = int(callback.data.split(":")[1])
        
        db = await get_db_async()
        try:
            order_service = OrderService(db)
            order = order_service.get_order_by_id(order_id)
            
            if not order:
                await callback.answer("❌ Заказ не найден", show_alert=True)
                return
            
            if order.user.telegram_id != callback.from_user.id:
                await callback.answer("❌ Это не ваш заказ", show_alert=True)
                return
            
            # Возвращаем статус на "новый" для пересмотра цены
            success = order_service.update_order_status(order_id, OrderStatus.NEW)
            
            if success:
                # Сохраняем данные для уведомлений до закрытия сессии
                order_data = {
                    'id': order.id,
                    'price': order.price,
                    'work_type': order.work_type,
                    'topic': order.topic,
                    'user_first_name': order.user.first_name,
                    'user_last_name': order.user.last_name,
                    'user_username': order.user.username
                }
                
                await callback.message.edit_text(
                    f"❌ <b>Вы отклонили цену {order_data['price']} ₽</b>\n\n"
                    f"📋 <b>Заказ #{order_data['id']}</b>\n"
                    f"📝 {order_data['work_type']}: {order_data['topic'][:50]}...\n\n"
                    f"🔄 Статус изменен на: <b>Новый</b>\n\n"
                    f"💭 Администратор пересмотрит цену и свяжется с вами.",
                    parse_mode="HTML",
                    reply_markup=get_order_status_keyboard(order_id)
                )
                
                # Уведомляем админа об отклонении цены
                await send_admin_notification_decline(order_data)
                
                await callback.answer("❌ Цена отклонена!")
            else:
                await callback.answer("❌ Ошибка обновления статуса", show_alert=True)
        finally:
            db.close()
                
    except Exception as e:
        print(f"Ошибка при отклонении цены: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)


@router.callback_query(F.data.startswith("view_order:"))
async def view_order_callback(callback: CallbackQuery, state: FSMContext):
    """Просмотр информации о заказе"""
    try:
        order_id = int(callback.data.split(":")[1])
        
        db = await get_db_async()
        try:
            order_service = OrderService(db)
            order = order_service.get_order_by_id(order_id)
            
            if not order:
                await callback.answer("❌ Заказ не найден", show_alert=True)
                return
            
            if order.user.telegram_id != callback.from_user.id:
                await callback.answer("❌ Это не ваш заказ", show_alert=True)
                return
            
            # Получаем emoji для статуса
            status_emoji = STATUS_EMOJI.get(order.status, "📋")
            
            # Формируем информацию о заказе
            order_info = f"📋 <b>Заказ #{order.id}</b>\n\n"
            order_info += f"📝 <b>Тип работы:</b> {order.work_type}\n"
            order_info += f"📚 <b>Предмет:</b> {order.subject}\n"
            order_info += f"📋 <b>Тема:</b> {order.topic}\n"
            order_info += f"📏 <b>Объем:</b> {order.volume}\n"
            order_info += f"⏰ <b>Срок:</b> {order.deadline}\n"
            
            if order.requirements:
                order_info += f"📌 <b>Требования:</b> {order.requirements[:200]}"
                if len(order.requirements) > 200:
                    order_info += "..."
                order_info += "\n"
            
            order_info += f"\n{status_emoji} <b>Статус:</b> {order.status.value}\n"
            
            if order.price:
                order_info += f"💰 <b>Цена:</b> {order.price} ₽\n"
            
            order_info += f"📅 <b>Создан:</b> {order.created_at.strftime('%d.%m.%Y %H:%M')}\n"
            
            # Показываем информацию
            await callback.message.edit_text(
                order_info,
                parse_mode="HTML",
                reply_markup=None
            )
            
            await callback.answer()
        finally:
            db.close()
            
    except Exception as e:
        print(f"Ошибка при просмотре заказа: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)


async def send_admin_notification_accept(order_data: dict):
    """Отправить уведомление админу о принятии цены"""
    try:
        from aiogram import Bot
        
        bot = Bot(token=settings.bot_token)
        
        admin_text = f"✅ <b>ЦЕНА ПРИНЯТА</b>\n\n"
        admin_text += f"📋 <b>Заказ #{order_data['id']}</b>\n"
        admin_text += f"👤 <b>Клиент:</b> {order_data['user_first_name']}"
        if order_data['user_last_name']:
            admin_text += f" {order_data['user_last_name']}"
        if order_data['user_username']:
            admin_text += f" (@{order_data['user_username']})"
        admin_text += f"\n💰 <b>Цена:</b> {order_data['price']} ₽\n"
        admin_text += f"📝 <b>Работа:</b> {order_data['work_type']}\n"
        admin_text += f"📋 <b>Тема:</b> {order_data['topic'][:100]}...\n\n"
        admin_text += f"🔗 <b>Админ-панель:</b> http://127.0.0.1:8000/orders/{order_data['id']}\n\n"
        admin_text += f"⏰ Статус изменен на: <b>Ожидает оплаты</b>"
        
        await bot.send_message(
            chat_id=settings.admin_user_id,
            text=admin_text,
            parse_mode="HTML"
        )
        
        print(f"✅ Уведомление о принятии цены отправлено админу")
        
        # Закрываем сессию бота
        await bot.session.close()
        
    except Exception as e:
        print(f"❌ Ошибка отправки уведомления админу о принятии: {e}")


async def send_admin_notification_decline(order_data: dict):
    """Отправить уведомление админу об отклонении цены"""
    try:
        from aiogram import Bot
        
        bot = Bot(token=settings.bot_token)
        
        admin_text = f"❌ <b>ЦЕНА ОТКЛОНЕНА</b>\n\n"
        admin_text += f"📋 <b>Заказ #{order_data['id']}</b>\n"
        admin_text += f"👤 <b>Клиент:</b> {order_data['user_first_name']}"
        if order_data['user_last_name']:
            admin_text += f" {order_data['user_last_name']}"
        if order_data['user_username']:
            admin_text += f" (@{order_data['user_username']})"
        admin_text += f"\n💰 <b>Отклоненная цена:</b> {order_data['price']} ₽\n"
        admin_text += f"📝 <b>Работа:</b> {order_data['work_type']}\n"
        admin_text += f"📋 <b>Тема:</b> {order_data['topic'][:100]}...\n\n"
        admin_text += f"🔗 <b>Админ-панель:</b> http://127.0.0.1:8000/orders/{order_data['id']}\n\n"
        admin_text += f"🔄 Статус изменен на: <b>Новый</b>\n"
        admin_text += f"💭 Требуется пересмотр цены!"
        
        await bot.send_message(
            chat_id=settings.admin_user_id,
            text=admin_text,
            parse_mode="HTML"
        )
        
        print(f"✅ Уведомление об отклонении цены отправлено админу")
        
        # Закрываем сессию бота
        await bot.session.close()
        
    except Exception as e:
        print(f"❌ Ошибка отправки уведомления админу об отклонении: {e}")