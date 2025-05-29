"""
Сервис для работы с платежами
"""
from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.config import settings
from app.database.models.order import Order
from app.database.models.payment import OrderPayment
from app.database.models.file import OrderFile
from app.database.models.enums import OrderStatus


class PaymentService:
    """Сервис для обработки платежей"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_payment_request(self, order_id: int) -> str:
        """
        Создать запрос на оплату и вернуть сообщение с реквизитами
        
        Args:
            order_id: ID заказа
            
        Returns:
            str: Текст сообщения с реквизитами
        """
        order = self.db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise ValueError(f"Заказ #{order_id} не найден")
        
        if not order.price:
            raise ValueError(f"Цена для заказа #{order_id} не установлена")
        
        # Создаем запись о платеже
        payment = OrderPayment(
            order_id=order_id,
            amount=order.price
        )
        self.db.add(payment)
        self.db.commit()
        
        # Формируем сообщение с реквизитами
        payment_message = f"""💰 <b>Заказ #{order_id} готов к оплате!</b>

📝 <b>Работа:</b> {order.work_type.replace('_', ' ').title()}
📋 <b>Тема:</b> {order.short_topic}
💵 <b>Сумма к оплате:</b> {order.price:,.2f} ₽

{settings.payment_instructions.format(
    card_number=settings.payment_card_number,
    phone=settings.payment_sbp_phone, 
    bank=settings.payment_bank_name,
    receiver=settings.payment_receiver_name,
    order_id=order_id
)}

🔍 <b>После оплаты пришлите скриншот чека!</b>
"""
        
        return payment_message
    
    def process_payment_screenshot(self, order_id: int, file_id: int, 
                                 user_message: str = None) -> bool:
        """
        Обработать скриншот оплаты от пользователя
        
        Args:
            order_id: ID заказа
            file_id: ID файла со скриншотом
            user_message: Сообщение пользователя
            
        Returns:
            bool: Успешно ли обработано
        """
        try:
            # Получаем заказ
            order = self.db.query(Order).filter(Order.id == order_id).first()
            if not order:
                return False
            
            # Получаем последний платеж по заказу
            payment = self.db.query(OrderPayment)\
                .filter(OrderPayment.order_id == order_id)\
                .order_by(OrderPayment.created_at.desc())\
                .first()
            
            if not payment:
                # Создаем новый платеж если его нет
                payment = OrderPayment(
                    order_id=order_id,
                    amount=order.price or 0
                )
                self.db.add(payment)
            
            # Привязываем скриншот к платежу
            payment.screenshot_file_id = file_id
            payment.screenshot_message = user_message
            
            self.db.commit()
            print(f"✅ Скриншот оплаты сохранен для заказа #{order_id}")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка обработки скриншота оплаты: {e}")
            self.db.rollback()
            return False
    
    def verify_payment(self, payment_id: int, admin_user_id: int) -> bool:
        """
        Подтвердить платеж
        
        Args:
            payment_id: ID платежа
            admin_user_id: ID администратора
            
        Returns:
            bool: Успешно ли подтверждено
        """
        try:
            payment = self.db.query(OrderPayment).filter(OrderPayment.id == payment_id).first()
            if not payment:
                return False
            
            payment.is_verified = True
            payment.is_rejected = False
            payment.verified_at = datetime.utcnow()
            
            # Меняем статус заказа на "отправлен"
            order = payment.order
            order.status = OrderStatus.SENT
            order.updated_at = datetime.utcnow()
            
            self.db.commit()
            print(f"✅ Платеж #{payment_id} подтвержден")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка подтверждения платежа: {e}")
            self.db.rollback()
            return False
    
    def reject_payment(self, payment_id: int, reason: str, admin_user_id: int) -> bool:
        """
        Отклонить платеж
        
        Args:
            payment_id: ID платежа
            reason: Причина отклонения
            admin_user_id: ID администратора
            
        Returns:
            bool: Успешно ли отклонено
        """
        try:
            payment = self.db.query(OrderPayment).filter(OrderPayment.id == payment_id).first()
            if not payment:
                return False
            
            payment.is_rejected = True
            payment.is_verified = False
            payment.rejection_reason = reason
            payment.rejected_at = datetime.utcnow()
            
            self.db.commit()
            print(f"✅ Платеж #{payment_id} отклонен")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка отклонения платежа: {e}")
            self.db.rollback()
            return False
    
    def get_pending_payments(self, limit: int = 20):
        """Получить платежи на проверке"""
        return self.db.query(OrderPayment)\
            .filter(
                OrderPayment.is_verified == False,
                OrderPayment.is_rejected == False,
                OrderPayment.screenshot_file_id.isnot(None)
            )\
            .order_by(OrderPayment.created_at.desc())\
            .limit(limit)\
            .all()
    
    def get_order_payments(self, order_id: int):
        """Получить все платежи по заказу"""
        return self.db.query(OrderPayment)\
            .filter(OrderPayment.order_id == order_id)\
            .order_by(OrderPayment.created_at.desc())\
            .all()
