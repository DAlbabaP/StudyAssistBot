# Создайте новый файл: app/bot/handlers/user_messages.py

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from app.services.user_service import UserService
from app.services.order_service import OrderService
from app.services.communication_service import CommunicationService
from app.services.payment_service import PaymentService
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


# === ОБРАБОТЧИКИ ФАЙЛОВ ===

@router.message(F.photo)
async def handle_user_photo(message: Message, state: FSMContext):
    """
    Обработчик фотографий от пользователя
    Особенно важно для скриншотов оплаты
    """
    # Проверяем, не находится ли пользователь в процессе создания заказа
    current_state = await state.get_state()
    if current_state:
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
          # Ищем заказ в статусе "ожидает оплаты"
        payment_orders = order_service.get_user_orders_by_status(
            user.id,  # Используем ID пользователя из БД, а не telegram_id
            OrderStatus.WAITING_PAYMENT
        )
        
        if payment_orders:
            # Есть заказ, ожидающий оплаты - это скорее всего скриншот оплаты
            order = payment_orders[0]  # Берем первый
              # Сохраняем фото
            from app.bot.utils.file_handler import save_photo
            from aiogram import Bot
            
            bot = Bot(token=settings.bot_token)
            
            try:
                # Получаем файл наибольшего размера
                photo = message.photo[-1]
                
                file_path, original_filename = await save_photo(photo, order.id, bot)
                  # Сохраняем в базу как файл заказа
                file_record = order_service.add_file_to_order(
                    order.id,
                    original_filename or f"screenshot_{photo.file_id}.jpg",
                    file_path,
                    photo.file_size
                )
                
                # Обрабатываем как скриншот оплаты
                from app.services.payment_service import PaymentService
                payment_service = PaymentService(db)
                
                caption = message.caption if message.caption else "Скриншот оплаты"
                payment_service.process_payment_screenshot(
                    order.id, 
                    file_record.id, 
                    caption
                )
                
                # Отправляем подтверждение пользователю
                await message.answer(
                    f"✅ <b>Скриншот оплаты получен!</b>\n\n"
                    f"📋 <b>Заказ #{order.id}</b>\n"
                    f"📝 <b>Тема:</b> {order.short_topic}\n\n"
                    f"⏳ Ваш платеж будет проверен в течение 1-2 часов.\n"
                    f"После подтверждения оплаты мы отправим готовую работу.",
                    parse_mode="HTML",
                    reply_markup=get_main_menu()
                )
                
                # Уведомляем админа о скриншоте оплаты
                await notify_admin_about_payment_screenshot(order, user, caption)
                
            finally:
                await bot.session.close()
        
        else:            # Нет заказов в ожидании оплаты - обрабатываем как обычный файл
            active_orders = order_service.get_user_orders_by_status(
                user.id,  # Используем ID пользователя из БД, а не telegram_id
                [OrderStatus.NEW, OrderStatus.IN_PROGRESS, OrderStatus.REVISION]
            )
            
            if active_orders:
                order = active_orders[0]                # Сохраняем фото как обычный файл
                from app.bot.utils.file_handler import save_photo
                from aiogram import Bot
                
                bot = Bot(token=settings.bot_token)
                
                try:
                    photo = message.photo[-1]
                    file_path, original_filename = await save_photo(photo, order.id, bot)
                    
                    file_record = order_service.add_file_to_order(
                        order.id,
                        original_filename or f"photo_{photo.file_id}.jpg",
                        file_path,
                        photo.file_size
                    )
                    
                    # Сохраняем сообщение
                    caption = message.caption if message.caption else "Фотография"
                    await communication_service.save_user_message(
                        order.id, 
                        f"📸 Отправил фотографию: {caption}",
                        message.message_id
                    )
                    
                    await message.answer(
                        f"✅ <b>Фотография получена!</b>\n\n"
                        f"📋 <b>Заказ #{order.id}</b>\n"
                        f"📝 <b>Тема:</b> {order.short_topic}\n\n"
                        f"📄 <b>Файл:</b> {file_record.filename}",
                        parse_mode="HTML",
                        reply_markup=get_main_menu()
                    )
                    
                    # Уведомляем админа
                    await notify_admin_about_user_file(order, user, file_record)
                    
                finally:
                    await bot.session.close()
            
            else:
                await message.answer(
                    "❌ У вас нет активных заказов.\n\n"
                    "Создайте новый заказ, чтобы прикрепить файлы.",
                    reply_markup=get_main_menu()
                )
                
    except Exception as e:
        print(f"❌ Ошибка обработки фотографии: {e}")
        await message.answer(
            "❌ Произошла ошибка при обработке фотографии. Попробуйте еще раз.",
            reply_markup=get_main_menu()
        )
    finally:
        db.close()


@router.message(F.document)
async def handle_user_document(message: Message, state: FSMContext):
    """
    Обработчик документов от пользователя
    """
    # Проверяем, не находится ли пользователь в процессе создания заказа
    current_state = await state.get_state()
    if current_state:
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
        
        # Ищем активный заказ
        active_orders = order_service.get_user_orders_by_status(
            user.id,
            [OrderStatus.NEW, OrderStatus.IN_PROGRESS, OrderStatus.REVISION, OrderStatus.WAITING_PAYMENT]
        )
        
        if active_orders:
            order = active_orders[0]
            
            # Сохраняем документ
            from app.bot.utils.file_handler import save_file
            from aiogram import Bot
            
            bot = Bot(token=settings.bot_token)
            
            try:
                document = message.document
                file_path, original_filename = await save_file(document, order.id, bot)
                
                file_record = order_service.add_file_to_order(
                    order.id,
                    original_filename or document.file_name,
                    file_path,
                    document.file_size
                )
                
                # Сохраняем сообщение
                caption = message.caption if message.caption else f"Документ: {document.file_name}"
                await communication_service.save_user_message(
                    order.id, 
                    f"📎 Отправил документ: {caption}",
                    message.message_id
                )
                
                await message.answer(
                    f"✅ <b>Документ получен!</b>\n\n"
                    f"📋 <b>Заказ #{order.id}</b>\n"
                    f"📝 <b>Тема:</b> {order.short_topic}\n\n"
                    f"📄 <b>Файл:</b> {file_record.filename}",
                    parse_mode="HTML",
                    reply_markup=get_main_menu()
                )
                
                # Уведомляем админа
                await notify_admin_about_user_file(order, user, file_record)
                
            finally:
                await bot.session.close()
        
        else:
            await message.answer(
                "❌ У вас нет активных заказов.\n\n"
                "Создайте новый заказ, чтобы прикрепить файлы.",
                reply_markup=get_main_menu()
            )
                
    except Exception as e:
        print(f"❌ Ошибка обработки документа: {e}")
        await message.answer(
            "❌ Произошла ошибка при обработке файла. Попробуйте еще раз.",
            reply_markup=get_main_menu()
        )
    finally:
        db.close()


async def notify_admin_about_payment_screenshot(order, user, message_text: str):
    """
    Отправить уведомление админу о получении скриншота оплаты
    """
    try:
        from aiogram import Bot
        
        bot = Bot(token=settings.bot_token)
        
        admin_text = f"💰 <b>ПОЛУЧЕН СКРИНШОТ ОПЛАТЫ!</b>\n\n"
        admin_text += f"👤 <b>Пользователь:</b> {user.full_name}\n"
        admin_text += f"📱 <b>Telegram:</b> @{user.username or 'без username'}\n\n"
        admin_text += f"📋 <b>Заказ #{order.id}</b>\n"
        admin_text += f"📝 <b>{order.work_type}:</b> {order.short_topic}\n"
        admin_text += f"💵 <b>Сумма:</b> {order.price:,.2f} ₽\n\n"
        if message_text and message_text != "Скриншот оплаты":
            admin_text += f"💭 <b>Сообщение:</b> {message_text}\n\n"
        admin_text += f"🔗 <b>Проверить платеж:</b> http://127.0.0.1:8000/orders/{order.id}"
        
        await bot.send_message(
            chat_id=settings.admin_user_id,
            text=admin_text,
            parse_mode="HTML"
        )
        
        await bot.session.close()
        print(f"✅ Админ уведомлен о скриншоте оплаты для заказа #{order.id}")
        
    except Exception as e:
        print(f"❌ Ошибка уведомления админа о скриншоте: {e}")


async def notify_admin_about_user_file(order, user, file_record):
    """Уведомить администратора о получении файла от пользователя"""
    try:
        from aiogram import Bot
        
        bot = Bot(token=settings.bot_token)
        
        admin_text = f"📎 <b>НОВЫЙ ФАЙЛ ОТ ПОЛЬЗОВАТЕЛЯ</b>\n\n"
        admin_text += f"👤 <b>Пользователь:</b> {user.full_name}\n"
        admin_text += f"📱 <b>Telegram:</b> @{user.username or 'без username'}\n\n"
        admin_text += f"📋 <b>Заказ #{order.id}</b>\n"
        admin_text += f"📝 <b>{order.work_type}:</b> {order.short_topic}\n\n"
        admin_text += f"📄 <b>Файл:</b> {file_record.filename}\n"
        if file_record.file_size:
            admin_text += f"📊 <b>Размер:</b> {file_record.size_mb} МБ\n"
        admin_text += f"🔗 <b>Посмотреть:</b> http://127.0.0.1:8000/orders/{order.id}"
        
        await bot.send_message(
            chat_id=settings.admin_user_id,
            text=admin_text,
            parse_mode="HTML"
        )
        
        await bot.session.close()
        print(f"✅ Админ уведомлен о новом файле для заказа #{order.id}")
        
    except Exception as e:
        print(f"❌ Ошибка уведомления админа о файле: {e}")