from aiogram import Router, F
from aiogram.types import Message, Document
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from app.bot.states.states import OrderStates
from app.bot.keyboards.client import (
    get_work_types, get_cancel_keyboard, get_skip_keyboard, 
    get_files_keyboard, get_confirm_keyboard, get_main_menu
)
from app.bot.utils.text_formatter import format_work_type, format_order_summary
from app.bot.utils.file_handler import save_file, is_allowed_file_type, format_file_size
from app.services.user_service import UserService
from app.services.order_service import OrderService
from app.database.connection import get_db_async
from app.config import settings

router = Router()


@router.message(F.text == "📝 Новый заказ")
async def new_order_start(message: Message, state: FSMContext):
    """Начать создание нового заказа"""
    await state.clear()
    await state.set_state(OrderStates.WORK_TYPE)
    
    text = "📝 <b>Создание нового заказа</b>\n\n"
    text += "Выберите тип работы, которую нужно выполнить:"
    
    await message.answer(
        text,
        reply_markup=get_work_types(),
        parse_mode="HTML"
    )


@router.message(StateFilter(OrderStates.WORK_TYPE))
async def process_work_type(message: Message, state: FSMContext):
    """Обработка выбора типа работы"""
    if message.text == "🔙 Назад":
        await state.clear()
        await message.answer(
            "❌ Создание заказа отменено",
            reply_markup=get_main_menu()
        )
        return
    
    # Список доступных типов работ
    work_types = [
        "📚 Реферат", "📄 Курсовая работа", "🎓 Дипломная работа",
        "📝 Эссе", "🧮 Контрольная работа", "📊 Отчет по практике",
        "🔬 Лабораторная работа", "📋 Другое"
    ]
    
    if message.text not in work_types:
        await message.answer(
            "❌ Пожалуйста, выберите тип работы из предложенных вариантов",
            reply_markup=get_work_types()
        )
        return
    
    # Сохраняем выбранный тип работы
    await state.update_data(work_type=format_work_type(message.text))
    await state.set_state(OrderStates.SUBJECT)
    
    await message.answer(
        "📚 <b>Укажите предмет</b>\n\nНапример: Математика, История, Программирование",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )


@router.message(StateFilter(OrderStates.SUBJECT))
async def process_subject(message: Message, state: FSMContext):
    """Обработка ввода предмета"""
    if message.text == "❌ Отменить":
        await state.clear()
        await message.answer(
            "❌ Создание заказа отменено",
            reply_markup=get_main_menu()
        )
        return
    
    if len(message.text) < 2:
        await message.answer(
            "❌ Название предмета слишком короткое. Попробуйте еще раз:",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    await state.update_data(subject=message.text)
    await state.set_state(OrderStates.TOPIC)
    
    await message.answer(
        "📋 <b>Укажите тему работы</b>\n\nОпишите тему максимально подробно",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )


@router.message(StateFilter(OrderStates.TOPIC))
async def process_topic(message: Message, state: FSMContext):
    """Обработка ввода темы"""
    if message.text == "❌ Отменить":
        await state.clear()
        await message.answer(
            "❌ Создание заказа отменено",
            reply_markup=get_main_menu()
        )
        return
    
    if len(message.text) < 5:
        await message.answer(
            "❌ Тема слишком короткая. Опишите тему более подробно:",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    await state.update_data(topic=message.text)
    await state.set_state(OrderStates.VOLUME)
    
    await message.answer(
        "📏 <b>Укажите объем работы</b>\n\nНапример: 20 страниц, 10 листов, 5000 слов",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )


@router.message(StateFilter(OrderStates.VOLUME))
async def process_volume(message: Message, state: FSMContext):
    """Обработка ввода объема"""
    if message.text == "❌ Отменить":
        await state.clear()
        await message.answer(
            "❌ Создание заказа отменено",
            reply_markup=get_main_menu()
        )
        return
    
    await state.update_data(volume=message.text)
    await state.set_state(OrderStates.DEADLINE)
    
    await message.answer(
        "⏰ <b>Укажите срок выполнения</b>\n\nНапример: до 15 мая, через неделю, к понедельнику",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )


@router.message(StateFilter(OrderStates.DEADLINE))
async def process_deadline(message: Message, state: FSMContext):
    """Обработка ввода срока"""
    if message.text == "❌ Отменить":
        await state.clear()
        await message.answer(
            "❌ Создание заказа отменено",
            reply_markup=get_main_menu()
        )
        return
    
    await state.update_data(deadline=message.text)
    await state.set_state(OrderStates.REQUIREMENTS)
    
    await message.answer(
        "📄 <b>Дополнительные требования</b>\n\n"
        "Укажите особые требования к работе, методические указания, "
        "требования к оформлению и т.д.\n\n"
        "Можете пропустить этот шаг, если особых требований нет.",
        reply_markup=get_skip_keyboard(),
        parse_mode="HTML"
    )


@router.message(StateFilter(OrderStates.REQUIREMENTS))
async def process_requirements(message: Message, state: FSMContext):
    """Обработка ввода требований"""
    if message.text == "❌ Отменить":
        await state.clear()
        await message.answer(
            "❌ Создание заказа отменено",
            reply_markup=get_main_menu()
        )
        return
    
    if message.text == "⏭️ Пропустить":
        requirements = None
    else:
        requirements = message.text
    
    await state.update_data(requirements=requirements)
    await state.set_state(OrderStates.FILES)
    
    await message.answer(
        "📎 <b>Прикрепите файлы</b>\n\n"
        "Можете прикрепить методические указания, примеры работ, "
        "дополнительные материалы.\n\n"
        "Поддерживаются: PDF, DOC, DOCX, TXT, JPG, PNG, ZIP и др.\n"
        "Максимальный размер файла: 20 МБ\n\n"
        "Когда закончите загрузку, нажмите 'Завершить загрузку'",
        reply_markup=get_files_keyboard(),
        parse_mode="HTML"
    )


@router.message(StateFilter(OrderStates.FILES), F.document)
async def process_file(message: Message, state: FSMContext):
    """Обработка загрузки файла"""
    document = message.document
    
    # Проверяем размер файла
    if document.file_size > 20 * 1024 * 1024:  # 20 МБ
        await message.answer(
            f"❌ Файл слишком большой ({format_file_size(document.file_size)})\n"
            f"Максимальный размер: 20 МБ"
        )
        return
    
    # Проверяем тип файла
    if document.file_name and not is_allowed_file_type(document.file_name):
        await message.answer(
            f"❌ Неподдерживаемый тип файла: {document.file_name}\n"
            f"Поддерживаются: PDF, DOC, DOCX, TXT, JPG, PNG, ZIP и др."
        )
        return
    
    # 🔥 ИСПРАВЛЕНО: Сохраняем Document объект целиком
    data = await state.get_data()
    files = data.get('files', [])
    
    files.append({
        'file_id': document.file_id,
        'filename': document.file_name or f"Файл_{len(files)+1}",
        'size': document.file_size,
        'mime_type': document.mime_type,
        'document': document  # 🔥 ВАЖНО: Сохраняем весь объект Document
    })
    
    await state.update_data(files=files)
    
    filename_display = document.file_name or f"Файл_{len(files)}"
    
    await message.answer(
        f"✅ Файл <b>{filename_display}</b> добавлен\n"
        f"📊 Размер: {format_file_size(document.file_size)}\n"
        f"📎 Всего файлов: {len(files)}",
        parse_mode="HTML"
    )


@router.message(StateFilter(OrderStates.FILES))
async def process_files_finish(message: Message, state: FSMContext):
    """Завершение загрузки файлов"""
    if message.text == "❌ Отменить":
        await state.clear()
        await message.answer(
            "❌ Создание заказа отменено",
            reply_markup=get_main_menu()
        )
        return
    
    if message.text == "✅ Завершить загрузку":
        await state.set_state(OrderStates.CONFIRM)
        
        # Показываем сводку заказа
        data = await state.get_data()
        summary = format_order_summary(data)
        
        await message.answer(
            summary,
            reply_markup=get_confirm_keyboard(),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            "📎 Отправьте файл или нажмите 'Завершить загрузку'",
            reply_markup=get_files_keyboard()
        )


@router.message(StateFilter(OrderStates.CONFIRM))
async def process_confirm(message: Message, state: FSMContext):
    """Подтверждение заказа"""
    if message.text == "❌ Отменить":
        await state.clear()
        await message.answer(
            "❌ Создание заказа отменено",
            reply_markup=get_main_menu()
        )
        return
    
    if message.text == "✏️ Редактировать":
        await state.set_state(OrderStates.WORK_TYPE)
        await message.answer(
            "✏️ Давайте заполним заказ заново.\n\nВыберите тип работы:",
            reply_markup=get_work_types()
        )
        return
    
    if message.text == "✅ Подтвердить заказ":
        # Создаем заказ в базе данных
        data = await state.get_data()
        
        db = await get_db_async()
        user_service = UserService(db)
        order_service = OrderService(db)
        
        try:
            # Получаем пользователя
            user = user_service.get_user_by_telegram_id(message.from_user.id)
            
            # Создаем заказ
            order = order_service.create_order(
                user_id=user.id,
                work_type=data['work_type'],
                subject=data['subject'],
                topic=data['topic'],
                volume=data['volume'],
                deadline=data['deadline'],
                requirements=data.get('requirements')
            )
            
            # 🔥 ИСПРАВЛЕНО: Правильное сохранение файлов
            files_saved = 0
            saved_files_info = []
            
            if data.get('files'):
                from aiogram import Bot
                
                bot = Bot(token=settings.bot_token)
                
                try:
                    for i, file_info in enumerate(data['files']):
                        try:
                            # 🔥 ИСПРАВЛЕНО: Используем сохраненный Document объект
                            document = file_info['document']
                            
                            # Сохраняем файл с правильным именем
                            saved_filename, file_path = await save_file(document, order.id, bot)
                            
                            # Определяем тип файла
                            file_type = None
                            if saved_filename and '.' in saved_filename:
                                file_type = saved_filename.split('.')[-1].lower()
                            
                            # Сохраняем информацию о файле в БД
                            order_file = order_service.add_file_to_order(
                                order_id=order.id,
                                filename=saved_filename,  # 🔥 Используем имя сохраненного файла
                                file_path=file_path,
                                file_size=document.file_size,
                                file_type=file_type
                            )
                            
                            files_saved += 1
                            saved_files_info.append({
                                'original': file_info['filename'],
                                'saved': saved_filename,
                                'path': file_path
                            })
                            
                            print(f"✅ Файл сохранен: {file_info['filename']} -> {saved_filename}")
                            
                        except Exception as e:
                            print(f"❌ Ошибка сохранения файла {file_info.get('filename', 'неизвестный')}: {e}")
                            continue
                    
                finally:
                    await bot.session.close()
            
            # Сохраняем данные для уведомления админа
            order_id = order.id
            user_data = {
                'first_name': user.first_name,
                'last_name': user.last_name,
                'username': user.username,
                'telegram_id': user.telegram_id
            }
            
        finally:
            db.close()
        
        await state.clear()
        
        # Формируем сообщение об успехе
        success_text = f"✅ <b>Заказ #{order_id} создан!</b>\n\n"
        success_text += "📋 Ваш заказ принят в обработку.\n"
        
        if files_saved > 0:
            success_text += f"📎 Прикреплено файлов: {files_saved}\n"
            success_text += "\n📁 <b>Сохраненные файлы:</b>\n"
            for file_info in saved_files_info:
                success_text += f"• {file_info['saved']}\n"
        
        success_text += "\n🔔 Вы получите уведомление при изменении статуса.\n"
        success_text += "📱 Посмотреть статус заказа можно в разделе 'Мои заказы'"
        
        await message.answer(
            success_text,
            reply_markup=get_main_menu(),
            parse_mode="HTML"
        )
        
        # Уведомляем администратора о новом заказе
        await send_admin_notification(order_id, user_data, data, files_saved, saved_files_info)
    
    else:
        await message.answer(
            "❌ Пожалуйста, выберите действие из предложенных вариантов",
            reply_markup=get_confirm_keyboard()
        )


async def send_admin_notification(order_id: int, user_data: dict, order_data: dict, files_count: int = 0, files_info: list = None):
    """Отправить уведомление администратору о новом заказе"""
    try:
        from aiogram import Bot
        
        bot = Bot(token=settings.bot_token)
        
        admin_text = f"🆕 <b>НОВЫЙ ЗАКАЗ #{order_id}</b>\n\n"
        admin_text += f"👤 <b>Клиент:</b> {user_data['first_name']}"
        if user_data['last_name']:
            admin_text += f" {user_data['last_name']}"
        if user_data['username']:
            admin_text += f" (@{user_data['username']})"
        admin_text += f"\n📱 <b>Telegram ID:</b> {user_data['telegram_id']}\n\n"
        
        admin_text += f"📝 <b>Тип работы:</b> {order_data['work_type']}\n"
        admin_text += f"📚 <b>Предмет:</b> {order_data['subject']}\n"
        admin_text += f"📋 <b>Тема:</b> {order_data['topic']}\n"
        admin_text += f"📏 <b>Объем:</b> {order_data['volume']}\n"
        admin_text += f"⏰ <b>Срок:</b> {order_data['deadline']}\n"
        
        if order_data.get('requirements'):
            requirements_preview = order_data['requirements'][:200]
            if len(order_data['requirements']) > 200:
                requirements_preview += "..."
            admin_text += f"📌 <b>Требования:</b> {requirements_preview}\n"
        
        if files_count > 0:
            admin_text += f"\n📎 <b>Файлов прикреплено:</b> {files_count}\n"
            if files_info:
                admin_text += "<b>Сохраненные файлы:</b>\n"
                for file_info in files_info[:5]:  # Показываем только первые 5 файлов
                    admin_text += f"• {file_info['saved']}\n"
                if len(files_info) > 5:
                    admin_text += f"• ... и еще {len(files_info) - 5} файлов\n"
        
        admin_text += f"\n🔗 <b>Админ-панель:</b> http://127.0.0.1:8000/orders/{order_id}\n"
        admin_text += f"\n💼 Заказ ожидает установки цены!"
        
        # Отправляем уведомление админу
        await bot.send_message(
            chat_id=settings.admin_user_id,
            text=admin_text,
            parse_mode="HTML"
        )
        
        print(f"✅ Уведомление о новом заказе #{order_id} отправлено админу")
        
        # Закрываем сессию бота
        await bot.session.close()
        
    except Exception as e:
        print(f"❌ Ошибка отправки уведомления админу: {e}")