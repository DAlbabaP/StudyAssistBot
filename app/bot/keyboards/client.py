from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from typing import List


def get_main_menu() -> ReplyKeyboardMarkup:
    """Главное меню клиента"""
    builder = ReplyKeyboardBuilder()
    builder.add(
        KeyboardButton(text="📝 Новый заказ"),
        KeyboardButton(text="📋 Мои заказы"),
        KeyboardButton(text="ℹ️ О нас"),
        KeyboardButton(text="☎️ Поддержка")
    )
    builder.adjust(2, 2)
    return builder.as_markup(resize_keyboard=True)


def get_work_types() -> ReplyKeyboardMarkup:
    """Клавиатура выбора типа работы"""
    builder = ReplyKeyboardBuilder()
    work_types = [
        "📚 Реферат",
        "📄 Курсовая работа",
        "🎓 Дипломная работа",
        "📝 Эссе",
        "🧮 Контрольная работа",
        "📊 Отчет по практике",
        "🔬 Лабораторная работа",
        "📋 Другое"
    ]
    
    for work_type in work_types:
        builder.add(KeyboardButton(text=work_type))
    
    builder.add(KeyboardButton(text="🔙 Назад"))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура отмены"""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="❌ Отменить"))
    return builder.as_markup(resize_keyboard=True)


def get_skip_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура пропуска (для необязательных полей)"""
    builder = ReplyKeyboardBuilder()
    builder.add(
        KeyboardButton(text="⏭️ Пропустить"),
        KeyboardButton(text="❌ Отменить")
    )
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)


def get_files_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для загрузки файлов"""
    builder = ReplyKeyboardBuilder()
    builder.add(
        KeyboardButton(text="✅ Завершить загрузку"),
        KeyboardButton(text="❌ Отменить")
    )
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)


def get_confirm_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура подтверждения заказа"""
    builder = ReplyKeyboardBuilder()
    builder.add(
        KeyboardButton(text="✅ Подтвердить заказ"),
        KeyboardButton(text="✏️ Редактировать"),
        KeyboardButton(text="❌ Отменить")
    )
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)


def get_contact_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для отправки контакта"""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="📱 Отправить контакт", request_contact=True))
    builder.add(KeyboardButton(text="❌ Отменить"))
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)


def get_price_response_keyboard(order_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для ответа на предложенную цену"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="✅ Принять цену",
            callback_data=f"accept_price:{order_id}"
        ),
        InlineKeyboardButton(
            text="❌ Отклонить",
            callback_data=f"decline_price:{order_id}"
        )
    )
    builder.adjust(1)
    return builder.as_markup()


def get_order_status_keyboard(order_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для просмотра статуса заказа"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="📋 Посмотреть заказ",
            callback_data=f"view_order:{order_id}"
        )
    )
    return builder.as_markup()
