"""
Модель для платежей
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime
from . import Base


class OrderPayment(Base):
    """Модель платежей по заказам"""
    __tablename__ = "order_payments"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    
    # Данные о платеже
    amount = Column(Numeric(10, 2), nullable=False)  # Сумма платежа
    payment_method = Column(String(50))  # Способ оплаты (card, sbp, etc.)
    transaction_id = Column(String(255))  # ID транзакции (если есть)
    
    # Скриншот чека
    screenshot_file_id = Column(Integer, ForeignKey("order_files.id"))
    screenshot_message = Column(Text)  # Сообщение от пользователя к скриншоту
    
    # Статус
    is_verified = Column(Boolean, default=False)  # Подтвержден ли платеж
    is_rejected = Column(Boolean, default=False)  # Отклонен ли платеж
    rejection_reason = Column(Text)  # Причина отклонения
    
    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow)
    verified_at = Column(DateTime)
    rejected_at = Column(DateTime)
    
    # Связи
    order = relationship("Order", back_populates="payments")
    screenshot_file = relationship("OrderFile")
    
    @property
    def status_text(self) -> str:
        """Текстовый статус платежа"""
        if self.is_verified:
            return "✅ Подтвержден"
        elif self.is_rejected:
            return "❌ Отклонен"
        else:
            return "⏳ На проверке"
    
    @property
    def amount_rub(self) -> str:
        """Сумма в рублях с форматированием"""
        return f"{self.amount:,.2f} ₽"
