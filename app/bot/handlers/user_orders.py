from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from app.bot.keyboards.client import get_main_menu
from app.bot.keyboards.inline import (
    get_orders_pagination_keyboard, get_order_details_keyboard, 
    get_order_action_keyboard
)
from app.bot.utils.text_formatter import format_order_list, format_order_info
from app.services.user_service import UserService
from app.services.order_service import OrderService
from app.database.connection import get_db_async

router = Router()


@router.message(F.text == "📋 Мои заказы")
async def my_orders(message: Message, state: FSMContext):
    """Показать заказы пользователя"""
    await state.clear()
    
    db = await get_db_async()
    user_service = UserService(db)
    order_service = OrderService(db)
    
    # Получаем пользователя
    user = user_service.get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer(
            "❌ Пользователь не найден. Используйте /start",
            reply_markup=get_main_menu()
        )
        db.close()
        return
    
    # Получаем заказы пользователя
    result = order_service.get_user_orders(user.id, page=1, per_page=5)
    
    db.close()
    
    if not result['orders']:
        await message.answer(
            "📭 <b>У вас пока нет заказов</b>\n\n"
            "Создайте первый заказ, нажав кнопку '📝 Новый заказ'",
            reply_markup=get_main_menu(),
            parse_mode="HTML"
        )
        return
    
    # Формируем текст со списком заказов
    text = format_order_list(result['orders'], result['page'], result['total_pages'])
    
    # Добавляем кнопки для каждого заказа
    keyboard = None
    if result['total_pages'] > 1:
        keyboard = get_orders_pagination_keyboard(
            result['page'], 
            result['total_pages'], 
            user.id
        )
    
    await message.answer(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("orders_page:"))
async def orders_pagination(callback: CallbackQuery):
    """Обработка пагинации заказов"""
    _, page_str, user_id_str = callback.data.split(":")
    page = int(page_str)
    
    db = await get_db_async()
    order_service = OrderService(db)
    
    if user_id_str == "all":
        # Админ смотрит все заказы
        result = order_service.get_orders_by_status(page=page, per_page=5)
    else:
        # Пользователь смотрит свои заказы
        user_id = int(user_id_str)
        result = order_service.get_user_orders(user_id, page=page, per_page=5)
    
    db.close()
    
    if not result['orders']:
        await callback.answer("Заказы не найдены")
        return
    
    text = format_order_list(result['orders'], result['page'], result['total_pages'])
    
    keyboard = None
    if result['total_pages'] > 1:
        keyboard = get_orders_pagination_keyboard(
            result['page'], 
            result['total_pages'],
            int(user_id_str) if user_id_str != "all" else None
        )
    
    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("order_details:"))
async def order_details(callback: CallbackQuery):
    """Показать детальную информацию о заказе"""
    order_id = int(callback.data.split(":")[1])
    
    db = await get_db_async()
    order_service = OrderService(db)
    user_service = UserService(db)
    
    order = order_service.get_order_by_id(order_id)
    
    if not order:
        await callback.answer("Заказ не найден")
        db.close()
        return
    
    # Проверяем права доступа
    user = user_service.get_user_by_telegram_id(callback.from_user.id)
    is_admin = callback.from_user.id == settings.admin_id
    
    if not is_admin and (not user or order.user_id != user.id):
        await callback.answer("У вас нет доступа к этому заказу")
        db.close()
        return
    
    db.close()
    
    # Формируем детальную информацию
    if is_admin:
        from app.bot.utils.text_formatter import format_admin_order_info
        text = format_admin_order_info(order)
    else:
        text = format_order_info(order, detailed=True)
    
    # Добавляем информацию о файлах
    if order.files:
        text += f"\n📎 <b>Прикрепленные файлы:</b>\n"
        for file in order.files:
            from app.bot.utils.file_handler import get_file_type_emoji, format_file_size
            emoji = get_file_type_emoji(file.filename)
            size = format_file_size(file.file_size) if file.file_size else "неизвестно"
            text += f"{emoji} {file.filename} ({size})\n"
    
    keyboard = get_order_details_keyboard(order_id, is_admin)
    
    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_orders")
async def back_to_orders(callback: CallbackQuery):
    """Вернуться к списку заказов"""
    # Определяем, это админ или пользователь
    is_admin = callback.from_user.id == settings.admin_id
    
    db = await get_db_async()
    order_service = OrderService(db)
    
    if is_admin:
        result = order_service.get_orders_by_status(page=1, per_page=5)
    else:
        user_service = UserService(db)
        user = user_service.get_user_by_telegram_id(callback.from_user.id)
        result = order_service.get_user_orders(user.id, page=1, per_page=5)
    
    db.close()
    
    text = format_order_list(result['orders'], result['page'], result['total_pages'])
    
    keyboard = None
    if result['total_pages'] > 1:
        keyboard = get_orders_pagination_keyboard(
            result['page'], 
            result['total_pages'],
            None if is_admin else user.id
        )
    
    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "current_page")
async def current_page_callback(callback: CallbackQuery):
    """Заглушка для кнопки текущей страницы"""
    await callback.answer("Вы находитесь на этой странице")
