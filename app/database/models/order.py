from sqlalchemy import Column, Integer, String, Text, DateTime, Numeric, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from . import Base
from .enums import OrderStatus


class Order(Base):
    """Модель заказа на учебную работу"""
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    work_type = Column(String(50), nullable=False)
    subject = Column(String(200), nullable=False)
    topic = Column(Text, nullable=False)
    volume = Column(String(100), nullable=False)
    deadline = Column(String(200), nullable=False)  # Храним как строку, т.к. может быть "до среды"
    requirements = Column(Text, nullable=True)
    status = Column(Enum(OrderStatus), default=OrderStatus.NEW)
    price = Column(Numeric(10, 2), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="orders")
    files = relationship("OrderFile", back_populates="order", cascade="all, delete-orphan")
    status_history = relationship("StatusHistory", back_populates="order", cascade="all, delete-orphan")
    messages = relationship("OrderMessage", back_populates="order", cascade="all, delete-orphan")  # 🆕 НОВОЕ
    
    def __repr__(self):
        return f"<Order(id={self.id}, work_type='{self.work_type}', status='{self.status}')>"
    
    @property
    def short_topic(self):
        """Сокращенная тема для отображения"""
        return self.topic[:50] + "..." if len(self.topic) > 50 else self.topic
    
    @property
    def files_count(self):
        """Количество файлов в заказе"""
        return len(self.files) if self.files else 0
    
    @property
    def client_files_count(self):
        """Количество файлов от клиента"""
        return len([f for f in self.files if not f.uploaded_by_admin]) if self.files else 0
    
    @property
    def admin_files_count(self):
        """Количество файлов от админа"""
        return len([f for f in self.files if f.uploaded_by_admin]) if self.files else 0
    
    @property
    def messages_count(self):
        """Количество сообщений по заказу"""
        return len(self.messages) if self.messages else 0
    
    @property
    def last_message(self):
        """Последнее сообщение по заказу"""
        if self.messages:
            return sorted(self.messages, key=lambda m: m.sent_at, reverse=True)[0]
        return None