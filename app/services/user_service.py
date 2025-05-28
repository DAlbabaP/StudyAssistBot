from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.database.models.user import User
from typing import Optional, List


class UserService:
    """Сервис для работы с пользователями"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Получить пользователя по Telegram ID"""
        return self.db.query(User).filter(User.telegram_id == telegram_id).first()
    
    def create_user(self, telegram_id: int, username: str = None, 
                   first_name: str = None, last_name: str = None) -> User:
        """Создать нового пользователя"""
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def update_user(self, user: User, **kwargs) -> User:
        """Обновить данные пользователя"""
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def get_or_create_user(self, telegram_id: int, username: str = None,
                          first_name: str = None, last_name: str = None) -> User:
        """Получить или создать пользователя"""
        user = self.get_user_by_telegram_id(telegram_id)
        if not user:
            user = self.create_user(telegram_id, username, first_name, last_name)
        else:
            # Обновляем данные если они изменились
            update_data = {}
            if username and user.username != username:
                update_data['username'] = username
            if first_name and user.first_name != first_name:
                update_data['first_name'] = first_name
            if last_name and user.last_name != last_name:
                update_data['last_name'] = last_name
            
            if update_data:
                user = self.update_user(user, **update_data)
        
        return user
    
    def block_user(self, telegram_id: int) -> bool:
        """Заблокировать пользователя"""
        user = self.get_user_by_telegram_id(telegram_id)
        if user:
            user.is_blocked = True
            self.db.commit()
            return True
        return False
    
    def unblock_user(self, telegram_id: int) -> bool:
        """Разблокировать пользователя"""
        user = self.get_user_by_telegram_id(telegram_id)
        if user:
            user.is_blocked = False
            self.db.commit()
            return True
        return False
    
    def get_all_users(self, include_blocked: bool = False) -> List[User]:
        """Получить всех пользователей"""
        query = self.db.query(User)
        if not include_blocked:
            query = query.filter(User.is_blocked == False)
        return query.all()
    
    def get_users_count(self, include_blocked: bool = False) -> int:
        """Получить количество пользователей"""
        query = self.db.query(User)
        if not include_blocked:
            query = query.filter(User.is_blocked == False)
        return query.count()
