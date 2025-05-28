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
    
    class Config:
        env_file = ".env"


settings = Settings()