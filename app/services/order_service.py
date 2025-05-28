from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from app.database.models.order import Order
from app.database.models.file import OrderFile
from app.database.models.status_history import StatusHistory
from app.database.models import OrderStatus
from app.database.models.user import User
from typing import Optional, List, Dict, Any
from datetime import datetime
import math


class OrderService:
    """Сервис для работы с заказами"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_order(self, user_id: int, work_type: str, subject: str, 
                    topic: str, volume: str, deadline: str, 
                    requirements: str = None) -> Order:
        """Создать новый заказ"""
        order = Order(
            user_id=user_id,
            work_type=work_type,
            subject=subject,
            topic=topic,
            volume=volume,
            deadline=deadline,
            requirements=requirements,
            status=OrderStatus.NEW
        )
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)
        
        # Добавляем запись в историю статусов
        self.add_status_history(order.id, None, OrderStatus.NEW, "Заказ создан")
        
        return order
    
    def get_order_by_id(self, order_id: int) -> Optional[Order]:
        """Получить заказ по ID"""
        return self.db.query(Order).filter(Order.id == order_id).first()
    
    def get_user_orders(self, user_id: int, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """Получить заказы пользователя с пагинацией"""
        query = self.db.query(Order).filter(Order.user_id == user_id).order_by(desc(Order.created_at))
        
        total = query.count()
        orders = query.offset((page - 1) * per_page).limit(per_page).all()
        
        return {
            'orders': orders,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': math.ceil(total / per_page) if total > 0 else 1        }

    def get_orders_by_status(self, status: OrderStatus = None, page: int = 1, 
                           per_page: int = 10) -> Dict[str, Any]:
        """Получить заказы по статусу"""
        query = self.db.query(Order).order_by(desc(Order.created_at))
        
        if status:
            query = query.filter(Order.status == status)
        
        total = query.count()
        orders = query.offset((page - 1) * per_page).limit(per_page).all()
        
        return {
            'orders': orders,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': math.ceil(total / per_page) if total > 0 else 1
        }

    def update_order_status(self, order_id: int, new_status: OrderStatus, note: str = None) -> bool:
        """Обновить статус заказа"""
        order = self.get_order_by_id(order_id)
        if not order:
            return False

        old_status = order.status
        order.status = new_status
        order.updated_at = datetime.utcnow()
        
        self.db.commit()
        # Добавляем запись в историю
        self.add_status_history(order_id, old_status, new_status, note)
        
        return True

    def update_order_price(self, order_id: int, price: float) -> bool:
        """Установить цену заказа"""
        order = self.get_order_by_id(order_id)
        if not order:
            return False

        old_price = order.price
        order.price = price
        order.updated_at = datetime.utcnow()
        self.db.commit()
          # Отправляем уведомление пользователю о новой цене
        self._send_price_notification(order, old_price, price)
        
        return True
    
    def _send_price_notification(self, order: Order, old_price: float, new_price: float):
        """Отправить уведомление пользователю о установке/изменении цены"""
        try:
            import asyncio
            import threading
            from app.bot.bot import bot
            from app.bot.keyboards.client import get_price_response_keyboard
            
            # Сохраняем данные до возможной потери связи с сессией
            user_telegram_id = order.user.telegram_id
            order_id = order.id
            work_type = order.work_type
            topic = order.topic
            
            # Формируем текст уведомления
            if old_price is None:
                notification_text = f"💰 <b>Цена установлена для вашего заказа!</b>\n\n"
            else:
                notification_text = f"💰 <b>Цена изменена для вашего заказа!</b>\n\n"
            
            notification_text += f"📋 <b>Заказ #{order_id}</b>\n"
            notification_text += f"📝 <b>Тип работы:</b> {work_type}\n"
            notification_text += f"📋 <b>Тема:</b> {topic[:50]}...\n\n"
            
            if old_price is not None:
                notification_text += f"💰 <b>Старая цена:</b> {old_price} ₽\n"
            
            notification_text += f"💰 <b>Новая цена:</b> {new_price} ₽\n\n"
            notification_text += f"❓ <b>Принимаете предложенную цену?</b>"
            
            # Отправляем уведомление асинхронно в отдельном потоке
            def send_notification_sync():
                async def send_notification():
                    try:
                        await bot.send_message(
                            chat_id=user_telegram_id,
                            text=notification_text,
                            parse_mode="HTML",
                            reply_markup=get_price_response_keyboard(order_id)
                        )
                        print(f"✅ Уведомление о цене отправлено пользователю {user_telegram_id}")
                    except Exception as e:
                        print(f"❌ Ошибка отправки уведомления о цене пользователю {user_telegram_id}: {e}")
                
                # Создаем новый event loop для потока
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(send_notification())
                finally:
                    loop.close()
              # Запускаем в отдельном потоке
            thread = threading.Thread(target=send_notification_sync)
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            print(f"❌ Ошибка при отправке уведомления о цене: {e}")
    
    def add_status_history(self, order_id: int, old_status: OrderStatus, 
                          new_status: OrderStatus, note: str = None):
        """Добавить запись в историю статусов"""
        history = StatusHistory(
            order_id=order_id,
            old_status=old_status,
            new_status=new_status,
            note=note
        )
        self.db.add(history)
        self.db.commit()
    
    def add_file_to_order(self, order_id: int, filename: str, file_path: str, 
                         file_size: int = None, file_type: str = None) -> OrderFile:
        """Добавить файл к заказу"""
        order_file = OrderFile(
            order_id=order_id,
            filename=filename,
            file_path=file_path,
            file_size=file_size,
            file_type=file_type
        )
        self.db.add(order_file)
        self.db.commit()
        self.db.refresh(order_file)
        return order_file
    
    def get_order_files(self, order_id: int) -> List[OrderFile]:
        """Получить файлы заказа"""
        return self.db.query(OrderFile).filter(OrderFile.order_id == order_id).all()
    
    def get_orders_statistics(self) -> Dict[str, Any]:
        """Получить статистику заказов"""
        total_orders = self.db.query(Order).count()
        
        stats = {
            'total_orders': total_orders,
            'by_status': {}
        }
        
        for status in OrderStatus:
            count = self.db.query(Order).filter(Order.status == status).count()
            stats['by_status'][status.value] = count
        
        return stats
    
    def search_orders(self, query: str, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """Поиск заказов по тексту"""
        search_query = self.db.query(Order).filter(
            or_(
                Order.topic.ilike(f'%{query}%'),
                Order.subject.ilike(f'%{query}%'),
                Order.work_type.ilike(f'%{query}%')
            )
        ).order_by(desc(Order.created_at))
        
        total = search_query.count()
        orders = search_query.offset((page - 1) * per_page).limit(per_page).all()
        
        return {
            'orders': orders,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': math.ceil(total / per_page) if total > 0 else 1
        }
