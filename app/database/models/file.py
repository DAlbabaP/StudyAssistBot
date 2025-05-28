from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from . import Base


class OrderFile(Base):
    """Модель файла, прикрепленного к заказу"""
    __tablename__ = "order_files"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)
    file_type = Column(String(50), nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    order = relationship("Order", back_populates="files")
    
    def __repr__(self):
        return f"<OrderFile(id={self.id}, filename='{self.filename}', order_id={self.order_id})>"
    
    @property
    def size_mb(self):
        """Размер файла в мегабайтах"""
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return 0
    
    @property
    def file_extension(self):
        """Расширение файла"""
        return self.filename.split('.')[-1].lower() if '.' in self.filename else ''
