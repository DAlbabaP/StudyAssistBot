from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Bot
    bot_token: str
    admin_user_id: int
    
    # Database
    database_url: str
    
    # Redis
    redis_url: Optional[str] = None
    
    # Files
    upload_path: str = "./uploads/"
    max_file_size: int = 20971520  # 20 MB
    
    # Admin Panel
    secret_key: str
    admin_host: str = "127.0.0.1"
    admin_port: int = 8000
    debug: bool = False
      # Payment
    tbank_api_key: Optional[str] = None
    
    # Payment Details
    payment_card_number: str = "1234 5678 9012 3456"
    payment_bank_name: str = "Тинькофф Банк"
    payment_receiver_name: str = "Иван Иванович И."
    payment_sbp_phone: str = "+7 (900) 123-45-67"
    payment_instructions: str = """📋 Инструкция по оплате:

1️⃣ Переведите указанную сумму любым удобным способом:
   💳 По номеру карты: {card_number}
   📱 По СБП (телефон): {phone}
   🏦 Банк: {bank}
   👤 Получатель: {receiver}

2️⃣ После оплаты отправьте скриншот чека
3️⃣ Мы проверим оплату и отправим готовую работу

❗️ Важно: в комментарии к переводу укажите номер заказа #{order_id}"""
    
    class Config:
        env_file = ".env"


settings = Settings()