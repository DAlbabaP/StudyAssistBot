from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from . import Base
from .enums import OrderStatus


class StatusHistory(Base):
    """Модель истории изменения статусов заказа"""
    __tablename__ = "status_history"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    old_status = Column(Enum(OrderStatus), nullable=True)
    new_status = Column(Enum(OrderStatus), nullable=False)
    changed_at = Column(DateTime, default=datetime.utcnow)
    note = Column(Text, nullable=True)
    
    # Relationships
    order = relationship("Order", back_populates="status_history")
    
    def __repr__(self):
        return f"<StatusHistory(id={self.id}, order_id={self.order_id}, {self.old_status} -> {self.new_status})>"
