from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, Document
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from app.bot.states.states import AdminStates
from app.bot.keyboards.inline import (
    get_admin_main_keyboard, get_status_change_keyboard,
    get_orders_pagination_keyboard, get_order_details_keyboard
)
from app.bot.keyboards.client import get_cancel_keyboard, get_main_menu
from app.bot.utils.text_formatter import format_order_list, format_admin_order_info
from app.services.user_service import UserService
from app.services.order_service import OrderService
from app.database.models import OrderStatus, get_status_text, get_status_emoji
from app.database.connection import get_db_async
from app.config import settings

router = Router()


def is_admin(user_id: int) -> bool:
    """Проверка, является ли пользователь администратором"""
    return user_id == settings.admin_id


@router.message(Command("admin"))
async def admin_panel(message: Message, state: FSMContext):
    """Открыть админ-панель"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к админ-панели")
        return
    
    await state.clear()
    
    db = await get_db_async()
    order_service = OrderService(db)
    user_service = UserService(db)
    
    # Получаем статистику
    stats = order_service.get_orders_statistics()
    users_count = user_service.get_users_count()
    
    db.close()
    
    admin_text = "👤 <b>Панель администратора</b>\n\n"
    admin_text += f"👥 Всего пользователей: {users_count}\n"
    admin_text += f"📋 Всего заказов: {stats['total_orders']}\n\n"
    admin_text += "<b>📊 Статистика по статусам:</b>\n"
    
    for status, count in stats['by_status'].items():
        status_text = get_status_text(OrderStatus(status))
        admin_text += f"• {status_text}: {count}\n"
    
    await message.answer(
        admin_text,
        reply_markup=get_admin_main_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("admin_orders:"))
async def admin_orders(callback: CallbackQuery):
    """Показать заказы админу"""
    status_filter = callback.data.split(":")[1]
    
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен")
        return
    
    db = await get_db_async()
    order_service = OrderService(db)
    
    # Определяем статус для фильтра
    status = None
    if status_filter != "all":
        status = OrderStatus(status_filter)
    
    result = order_service.get_orders_by_status(status, page=1, per_page=5)
    
    db.close()
    
    if not result['orders']:
        await callback.answer("Заказы не найдены")
        return
    
    # Заголовок в зависимости от фильтра
    titles = {
        "all": "Все заказы",
        "new": "Новые заказы",
        "in_progress": "Заказы в работе",
        "ready": "Готовые заказы"
    }
    
    text = f"📋 <b>{titles.get(status_filter, 'Заказы')}</b> (стр. 1/{result['total_pages']}):\n\n"
    
    for order in result['orders']:
        from app.database.models import get_status_emoji, get_status_text
        status_emoji = get_status_emoji(order.status)
        short_topic = order.topic[:30] + "..." if len(order.topic) > 30 else order.topic
        
        text += f"🆔 <b>#{order.id}</b> - {order.work_type}\n"
        text += f"👤 {order.user.full_name}\n"
        text += f"📋 {short_topic}\n"
        text += f"📊 {status_emoji} {get_status_text(order.status)}\n"
        
        if order.price:
            text += f"💰 {order.price} руб.\n"
        
        text += f"📅 {order.created_at.strftime('%d.%m.%Y')}\n"
        text += "➖➖➖➖➖➖➖➖➖➖\n"
    
    keyboard = None
    if result['total_pages'] > 1:
        keyboard = get_orders_pagination_keyboard(
            result['page'], 
            result['total_pages'], 
            None
        )
    
    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("set_price:"))
async def set_price_start(callback: CallbackQuery, state: FSMContext):
    """Начать установку цены заказа"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен")
        return
    
    order_id = int(callback.data.split(":")[1])
    
    await state.update_data(order_id=order_id)
    await state.set_state(AdminStates.SET_ORDER_PRICE)
    
    await callback.message.answer(
        f"💰 <b>Установка цены для заказа #{order_id}</b>\n\n"
        f"Введите цену в рублях (только число):",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(AdminStates.SET_ORDER_PRICE)
async def set_price_process(message: Message, state: FSMContext):
    """Обработка установки цены"""
    if message.text == "❌ Отменить":
        await state.clear()
        await message.answer(
            "❌ Установка цены отменена",
            reply_markup=get_main_menu()
        )
        return
    
    try:
        price = float(message.text.replace(",", "."))
        if price <= 0:
            raise ValueError("Цена должна быть положительной")
    except ValueError:
        await message.answer(
            "❌ Неверный формат цены. Введите число (например: 1500 или 1500.50):",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    data = await state.get_data()
    order_id = data['order_id']
    
    db = await get_db_async()
    order_service = OrderService(db)
    user_service = UserService(db)
    
    # Обновляем цену
    success = order_service.update_order_price(order_id, price)
    
    if success:
        order = order_service.get_order_by_id(order_id)
        db.close()
        
        await state.clear()
        await message.answer(
            f"✅ Цена для заказа #{order_id} установлена: {price} руб.",
            reply_markup=get_main_menu()
        )
        
        # Уведомляем клиента
        try:
            from aiogram import Bot
            bot = Bot(token=settings.bot_token)
            
            client_text = f"💰 <b>Цена установлена!</b>\n\n"
            client_text += f"Заказ #{order_id}: <b>{price} руб.</b>\n\n"
            client_text += "Для оплаты свяжитесь с нашим менеджером через кнопку 'Поддержка'"
            
            await bot.send_message(
                chat_id=order.user.telegram_id,
                text=client_text,
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"Ошибка отправки уведомления клиенту: {e}")
    else:
        db.close()
        await state.clear()
        await message.answer(
            f"❌ Ошибка установки цены для заказа #{order_id}",
            reply_markup=get_main_menu()
        )


@router.callback_query(F.data.startswith("change_status:"))
async def change_status_start(callback: CallbackQuery):
    """Показать меню изменения статуса"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен")
        return
    
    order_id = int(callback.data.split(":")[1])
    
    await callback.message.edit_text(
        f"🔄 <b>Изменение статуса заказа #{order_id}</b>\n\nВыберите новый статус:",
        reply_markup=get_status_change_keyboard(order_id),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("status:"))
async def change_status_process(callback: CallbackQuery):
    """Обработка изменения статуса"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен")
        return
    
    _, order_id_str, new_status_str = callback.data.split(":")
    order_id = int(order_id_str)
    new_status = OrderStatus(new_status_str)
    
    db = await get_db_async()
    order_service = OrderService(db)
    
    # Получаем заказ
    order = order_service.get_order_by_id(order_id)
    if not order:
        await callback.answer("Заказ не найден")
        db.close()
        return
    
    old_status = order.status
    
    # Обновляем статус
    success = order_service.update_order_status(
        order_id, 
        new_status, 
        f"Статус изменен администратором"
    )
    
    if success:
        order = order_service.get_order_by_id(order_id)  # Обновляем данные
        db.close()
        
        from app.database.models import get_status_text
        
        await callback.message.edit_text(
            f"✅ <b>Статус изменен!</b>\n\n"
            f"Заказ #{order_id}\n"
            f"Было: {get_status_text(old_status)}\n"
            f"Стало: {get_status_text(new_status)}",
            reply_markup=get_order_details_keyboard(order_id, True),
            parse_mode="HTML"
        )
        
        # Уведомляем клиента
        try:
            from aiogram import Bot
            bot = Bot(token=settings.bot_token)
            
            status_emoji = get_status_emoji(new_status)
            client_text = f"🔔 <b>Статус заказа изменен!</b>\n\n"
            client_text += f"Заказ #{order_id}\n"
            client_text += f"Новый статус: {status_emoji} {get_status_text(new_status)}"
            
            await bot.send_message(
                chat_id=order.user.telegram_id,
                text=client_text,
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"Ошибка отправки уведомления клиенту: {e}")
    else:
        db.close()
        await callback.message.edit_text(
            f"❌ Ошибка изменения статуса заказа #{order_id}",
            parse_mode="HTML"
        )
    
    await callback.answer()


@router.callback_query(F.data.startswith("send_file:"))
async def send_file_start(callback: CallbackQuery, state: FSMContext):
    """Начать отправку файла клиенту"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен")
        return
    
    order_id = int(callback.data.split(":")[1])
    
    await state.update_data(order_id=order_id)
    await state.set_state(AdminStates.SEND_ORDER_FILE)
    
    await callback.message.answer(
        f"📎 <b>Отправка файла для заказа #{order_id}</b>\n\n"
        f"Прикрепите файл, который нужно отправить клиенту:",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(AdminStates.SEND_ORDER_FILE, F.document)
async def send_file_process(message: Message, state: FSMContext):
    """Обработка отправки файла клиенту"""
    data = await state.get_data()
    order_id = data['order_id']
    
    db = await get_db_async()
    order_service = OrderService(db)
    
    order = order_service.get_order_by_id(order_id)
    if not order:
        await message.answer(
            f"❌ Заказ #{order_id} не найден",
            reply_markup=get_main_menu()
        )
        db.close()
        await state.clear()
        return
    
    db.close()
    
    # Отправляем файл клиенту
    try:
        from aiogram import Bot
        bot = Bot(token=settings.bot_token)
        
        client_text = f"📎 <b>Файл для заказа #{order_id}</b>\n\n"
        client_text += f"Ваша работа готова! Файл во вложении."
        
        await bot.send_document(
            chat_id=order.user.telegram_id,
            document=message.document.file_id,
            caption=client_text,
            parse_mode="HTML"
        )
        
        await state.clear()
        await message.answer(
            f"✅ Файл отправлен клиенту для заказа #{order_id}",
            reply_markup=get_main_menu()
        )
        
    except Exception as e:
        await state.clear()
        await message.answer(
            f"❌ Ошибка отправки файла: {e}",
            reply_markup=get_main_menu()
        )


@router.message(AdminStates.SEND_ORDER_FILE)
async def send_file_invalid(message: Message, state: FSMContext):
    """Обработка неверного типа сообщения при отправке файла"""
    if message.text == "❌ Отменить":
        await state.clear()
        await message.answer(
            "❌ Отправка файла отменена",
            reply_markup=get_main_menu()
        )
        return
    
    await message.answer(
        "❌ Пожалуйста, прикрепите файл или отмените операцию",
        reply_markup=get_cancel_keyboard()
    )


@router.callback_query(F.data == "admin_stats")
async def admin_statistics(callback: CallbackQuery):
    """Показать подробную статистику"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен")
        return
    
    db = await get_db_async()
    order_service = OrderService(db)
    user_service = UserService(db)
    
    stats = order_service.get_orders_statistics()
    users_count = user_service.get_users_count()
    
    db.close()
    
    stats_text = "📊 <b>Подробная статистика</b>\n\n"
    stats_text += f"👥 <b>Пользователи:</b> {users_count}\n"
    stats_text += f"📋 <b>Всего заказов:</b> {stats['total_orders']}\n\n"
    
    stats_text += "<b>📈 По статусам:</b>\n"
    for status, count in stats['by_status'].items():
        if count > 0:
            status_text = get_status_text(OrderStatus(status))
            percentage = round(count / stats['total_orders'] * 100, 1) if stats['total_orders'] > 0 else 0
            stats_text += f"• {status_text}: {count} ({percentage}%)\n"
    
    await callback.message.edit_text(
        stats_text,
        reply_markup=get_admin_main_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_start(callback: CallbackQuery, state: FSMContext):
    """Начать создание рассылки"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен")
        return
    
    await state.set_state(AdminStates.BROADCAST_MESSAGE)
    
    await callback.message.answer(
        "📢 <b>Создание рассылки</b>\n\n"
        "Введите текст сообщения для отправки всем пользователям:",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(AdminStates.BROADCAST_MESSAGE)
async def admin_broadcast_process(message: Message, state: FSMContext):
    """Обработка рассылки"""
    if message.text == "❌ Отменить":
        await state.clear()
        await message.answer(
            "❌ Рассылка отменена",
            reply_markup=get_main_menu()
        )
        return
    
    db = await get_db_async()
    user_service = UserService(db)
    
    users = user_service.get_all_users(include_blocked=False)
    db.close()
    
    if not users:
        await state.clear()
        await message.answer(
            "❌ Нет пользователей для рассылки",
            reply_markup=get_main_menu()
        )
        return
    
    # Отправляем рассылку
    success_count = 0
    failed_count = 0
    
    from aiogram import Bot
    bot = Bot(token=settings.bot_token)
    
    broadcast_text = f"📢 <b>Сообщение от администрации</b>\n\n{message.text}"
    
    for user in users:
        try:
            await bot.send_message(
                chat_id=user.telegram_id,
                text=broadcast_text,
                parse_mode="HTML"
            )
            success_count += 1
        except Exception as e:
            failed_count += 1
            print(f"Ошибка отправки пользователю {user.telegram_id}: {e}")
    
    await state.clear()
    
    result_text = f"📢 <b>Рассылка завершена!</b>\n\n"
    result_text += f"✅ Успешно отправлено: {success_count}\n"
    result_text += f"❌ Ошибок: {failed_count}\n"
    result_text += f"📊 Всего пользователей: {len(users)}"
    
    await message.answer(
        result_text,
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )
    
