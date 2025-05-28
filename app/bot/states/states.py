from aiogram.fsm.state import StatesGroup, State


class OrderStates(StatesGroup):
    """Состояния для создания заказа"""
    WORK_TYPE = State()      # Выбор типа работы
    SUBJECT = State()        # Ввод предмета
    TOPIC = State()          # Ввод темы
    VOLUME = State()         # Ввод объема
    DEADLINE = State()       # Ввод срока
    REQUIREMENTS = State()   # Ввод требований
    FILES = State()          # Загрузка файлов
    CONFIRM = State()        # Подтверждение заказа


class AdminStates(StatesGroup):
    """Состояния для админ-панели"""
    BROADCAST_MESSAGE = State()     # Отправка сообщения всем
    SET_ORDER_PRICE = State()       # Установка цены заказа
    SET_ORDER_STATUS = State()      # Изменение статуса заказа
    SEND_ORDER_FILE = State()       # Отправка файла клиенту
