from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.orm import Session

from app.bot.keyboards.client import get_main_menu, get_contact_keyboard
from app.services.user_service import UserService
from app.database.connection import get_db_async
from app.config import settings

router = Router()


@router.message(CommandStart())
async def start_command(message: Message, state: FSMContext):
    """Обработчик команды /start"""
    await state.clear()
    
    # Получаем или создаем пользователя
    db = await get_db_async()
    user_service = UserService(db)
    
    user = user_service.get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name
    )
    
    db.close()
    
    welcome_text = f"👋 <b>Добро пожаловать, {user.first_name or 'дорогой клиент'}!</b>\n\n"
    welcome_text += "🎓 Я помогу вам заказать качественную учебную работу.\n\n"
    welcome_text += "📝 <b>Что я умею:</b>\n"
    welcome_text += "• Принимать заказы на рефераты, курсовые, дипломы\n"
    welcome_text += "• Отслеживать статус выполнения работ\n"
    welcome_text += "• Уведомлять о готовности заказа\n"
    welcome_text += "• Принимать файлы и требования\n\n"
    welcome_text += "🚀 Выберите действие в меню ниже:"
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )


@router.message(Command("help"))
async def help_command(message: Message):
    """Обработчик команды /help"""
    help_text = "ℹ️ <b>Справка по использованию бота:</b>\n\n"
    help_text += "📝 <b>Создание заказа:</b>\n"
    help_text += "1. Нажмите 'Новый заказ'\n"
    help_text += "2. Выберите тип работы\n"
    help_text += "3. Укажите предмет и тему\n"
    help_text += "4. Опишите требования\n"
    help_text += "5. Прикрепите файлы (если нужно)\n"
    help_text += "6. Подтвердите заказ\n\n"
    help_text += "📋 <b>Просмотр заказов:</b>\n"
    help_text += "Нажмите 'Мои заказы' для просмотра списка\n\n"
    help_text += "🔔 <b>Уведомления:</b>\n"
    help_text += "Вы получите сообщение при изменении статуса заказа\n\n"
    help_text += "❓ <b>Нужна помощь?</b>\n"
    help_text += "Нажмите 'Поддержка' для связи с оператором"
    
    await message.answer(help_text, parse_mode="HTML")


@router.message(F.text == "ℹ️ О нас")
async def about_command(message: Message):
    """Информация о сервисе"""
    about_text = "🏢 <b>О нашем сервисе</b>\n\n"
    about_text += "🎓 Мы специализируемся на выполнении учебных работ:\n"
    about_text += "• Рефераты\n"
    about_text += "• Курсовые работы\n"
    about_text += "• Дипломные работы\n"
    about_text += "• Контрольные работы\n"
    about_text += "• Отчеты по практике\n"
    about_text += "• И многое другое\n\n"
    about_text += "⭐ <b>Наши преимущества:</b>\n"
    about_text += "✅ Высокое качество работ\n"
    about_text += "✅ Соблюдение сроков\n"
    about_text += "✅ Индивидуальный подход\n"
    about_text += "✅ Доступные цены\n"
    about_text += "✅ Гарантия уникальности\n\n"
    about_text += "📞 Связаться с нами можно через кнопку 'Поддержка'"
    
    await message.answer(about_text, parse_mode="HTML")


@router.message(F.text == "☎️ Поддержка")
async def support_command(message: Message):
    """Обработчик кнопки поддержки"""
    support_text = "📞 <b>Служба поддержки</b>\n\n"
    support_text += "Если у вас есть вопросы или нужна помощь, "
    support_text += "вы можете связаться с нашими операторами:\n\n"
    support_text += "📱 <b>Telegram:</b> @support_username\n"
    support_text += "📧 <b>Email:</b> support@example.com\n"
    support_text += "☎️ <b>Телефон:</b> +7 (xxx) xxx-xx-xx\n\n"
    support_text += "🕐 <b>Время работы:</b> Пн-Пт 9:00-18:00\n\n"
    support_text += "⚡ Мы стараемся отвечать в течение 30 минут!"
    
    await message.answer(support_text, parse_mode="HTML")


@router.message(F.text == "📱 Отправить контакт")
async def contact_received(message: Message):
    """Обработчик получения контакта"""
    if message.contact:
        # Сохраняем телефон пользователя
        db = await get_db_async()
        user_service = UserService(db)
        
        user = user_service.get_user_by_telegram_id(message.from_user.id)
        if user:
            user_service.update_user(user, phone=message.contact.phone_number)
        
        db.close()
        
        await message.answer(
            "✅ Спасибо! Ваш номер телефона сохранен.",
            reply_markup=get_main_menu()
        )
    else:
        await message.answer(
            "❌ Пожалуйста, отправьте контакт через кнопку",
            reply_markup=get_contact_keyboard()
        )
