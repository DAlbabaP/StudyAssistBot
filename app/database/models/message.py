from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from . import Base


class OrderMessage(Base):
    """Модель сообщений между админом и пользователем по заказу"""
    __tablename__ = "order_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    message_text = Column(Text, nullable=False)
    from_admin = Column(Boolean, default=False, nullable=False)  # True если от админа, False если от пользователя
    sent_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    delivered = Column(Boolean, default=False, nullable=False)   # Доставлено ли сообщение
    telegram_message_id = Column(Integer, nullable=True)         # ID сообщения в Telegram (для отслеживания)
    
    # Relationships
    order = relationship("Order", back_populates="messages")
    
    def __repr__(self):
        sender = "Admin" if self.from_admin else "User"
        return f"<OrderMessage(id={self.id}, order_id={self.order_id}, from={sender}, sent_at={self.sent_at})>"
    
    @property
    def sender_label(self):
        """Отправитель для отображения"""
        return "Администратор" if self.from_admin else "Клиент"
    
    @property
    def message_preview(self):
        """Превью сообщения (первые 50 символов)"""
        return self.message_text[:50] + "..." if len(self.message_text) > 50 else self.message_text