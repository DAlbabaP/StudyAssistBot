import os
import asyncio
from typing import Optional, List
from sqlalchemy.orm import Session
from aiogram import Bot
from aiogram.types import FSInputFile
from datetime import datetime
from pathlib import Path

from app.config import settings
from app.database.models.order import Order
from app.database.models.file import OrderFile
from app.database.models.message import OrderMessage


class CommunicationService:
    """Сервис для общения между админом и пользователями"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def send_message_to_user(self, order_id: int, message_text: str, from_admin: bool = True) -> bool:
        """
        Отправить сообщение пользователю через Telegram
        
        Args:
            order_id: ID заказа
            message_text: Текст сообщения
            from_admin: True если от админа
            
        Returns:
            bool: Успешно ли отправлено
        """
        try:
            # Получаем заказ
            order = self.db.query(Order).filter(Order.id == order_id).first()
            if not order:
                print(f"❌ Заказ #{order_id} не найден")
                return False
            
            # Создаем бота
            bot = Bot(token=settings.bot_token)
            
            try:
                # Формируем сообщение
                if from_admin:
                    formatted_message = f"💬 <b>Сообщение от администратора</b>\n\n"
                    formatted_message += f"📋 <b>Заказ #{order_id}</b>\n"
                    formatted_message += f"📝 {order.work_type}: {order.short_topic}\n\n"
                    formatted_message += f"<i>{message_text}</i>"
                else:
                    formatted_message = message_text
                
                # Отправляем сообщение
                telegram_message = await bot.send_message(
                    chat_id=order.user.telegram_id,
                    text=formatted_message,
                    parse_mode="HTML"
                )
                
                # Сохраняем в БД
                order_message = OrderMessage(
                    order_id=order_id,
                    message_text=message_text,
                    from_admin=from_admin,
                    delivered=True,
                    telegram_message_id=telegram_message.message_id
                )
                
                self.db.add(order_message)
                self.db.commit()
                
                print(f"✅ Сообщение отправлено пользователю {order.user.telegram_id} по заказу #{order_id}")
                return True
                
            finally:
                await bot.session.close()
                
        except Exception as e:
            print(f"❌ Ошибка отправки сообщения: {e}")
            
            # Сохраняем неотправленное сообщение
            try:
                order_message = OrderMessage(
                    order_id=order_id,
                    message_text=message_text,
                    from_admin=from_admin,
                    delivered=False
                )
                
                self.db.add(order_message)
                self.db.commit()
            except:
                pass
            
            return False
    
    async def send_file_to_user(self, order_id: int, file_id: int) -> bool:
        """
        Отправить файл пользователю через Telegram
        
        Args:
            order_id: ID заказа
            file_id: ID файла
            
        Returns:
            bool: Успешно ли отправлено
        """
        try:
            # Получаем заказ и файл
            order = self.db.query(Order).filter(Order.id == order_id).first()
            if not order:
                print(f"❌ Заказ #{order_id} не найден")
                return False
            
            file_record = self.db.query(OrderFile).filter(OrderFile.id == file_id).first()
            if not file_record:
                print(f"❌ Файл #{file_id} не найден")
                return False
            
            # Проверяем файл на диске
            if not os.path.exists(file_record.file_path):
                print(f"❌ Файл не найден на диске: {file_record.file_path}")
                return False
            
            # Создаем бота
            bot = Bot(token=settings.bot_token)
            
            try:
                # Формируем сообщение
                caption = f"📎 <b>Файл от администратора</b>\n\n"
                caption += f"📋 <b>Заказ #{order_id}</b>\n"
                caption += f"📝 {order.work_type}: {order.short_topic}\n\n"
                caption += f"📄 Файл: <b>{file_record.filename}</b>\n"
                if file_record.file_size:
                    caption += f"📊 Размер: {file_record.size_mb} MB"
                
                # Создаем файл для отправки
                input_file = FSInputFile(
                    path=file_record.file_path,
                    filename=file_record.filename
                )
                
                # Отправляем файл
                await bot.send_document(
                    chat_id=order.user.telegram_id,
                    document=input_file,
                    caption=caption,
                    parse_mode="HTML"
                )
                
                # Помечаем файл как отправленный
                file_record.sent_to_user = True
                file_record.sent_at = datetime.utcnow()
                self.db.commit()
                
                print(f"✅ Файл {file_record.filename} отправлен пользователю {order.user.telegram_id}")
                
                # Также отправляем уведомление в сообщениях
                await self.send_message_to_user(
                    order_id, 
                    f"📎 Отправлен файл: {file_record.filename}"
                )
                
                return True
                
            finally:
                await bot.session.close()
                
        except Exception as e:
            print(f"❌ Ошибка отправки файла: {e}")
            return False
    
    def get_order_messages(self, order_id: int) -> List[OrderMessage]:
        """Получить все сообщения по заказу"""
        return self.db.query(OrderMessage)\
            .filter(OrderMessage.order_id == order_id)\
            .order_by(OrderMessage.sent_at.desc())\
            .all()
    
    def save_admin_file(self, order_id: int, file_path: str, original_filename: str, 
                       file_size: int = None) -> OrderFile:
        """
        Сохранить файл загруженный админом
        
        Args:
            order_id: ID заказа
            file_path: Путь к сохраненному файлу
            original_filename: Оригинальное имя файла
            file_size: Размер файла
            
        Returns:
            OrderFile: Созданная запись файла
        """
        # Определяем тип файла
        file_type = None
        if '.' in original_filename:
            file_type = original_filename.split('.')[-1].lower()
        
        # Создаем запись в БД
        order_file = OrderFile(
            order_id=order_id,
            filename=original_filename,
            file_path=file_path,
            file_size=file_size,
            file_type=file_type,
            uploaded_by_admin=True,  # Помечаем как загруженный админом
            sent_to_user=False
        )
        
        self.db.add(order_file)
        self.db.commit()
        self.db.refresh(order_file)
        
        print(f"✅ Файл от админа сохранен: {original_filename} для заказа #{order_id}")
        return order_file
    # Обновите app/services/communication_service.py - добавьте эти методы:

    async def save_user_message(self, order_id: int, message_text: str, 
                               telegram_message_id: int = None) -> bool:
        """
        Сохранить сообщение от пользователя
        
        Args:
            order_id: ID заказа
            message_text: Текст сообщения
            telegram_message_id: ID сообщения в Telegram
            
        Returns:
            bool: Успешно ли сохранено
        """
        try:
            # Проверяем существование заказа
            order = self.db.query(Order).filter(Order.id == order_id).first()
            if not order:
                print(f"❌ Заказ #{order_id} не найден")
                return False
            
            # Сохраняем сообщение в БД
            order_message = OrderMessage(
                order_id=order_id,
                message_text=message_text,
                from_admin=False,  # От пользователя
                delivered=True,    # Считаем что дошло до нас
                telegram_message_id=telegram_message_id
            )
            
            self.db.add(order_message)
            self.db.commit()
            
            print(f"✅ Сообщение от пользователя сохранено для заказа #{order_id}")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка сохранения сообщения пользователя: {e}")
            self.db.rollback()
            return False
    
    def get_dialog_messages(self, order_id: int, limit: int = 50) -> List[OrderMessage]:
        """
        Получить все сообщения диалога по заказу (от админа и от пользователя)
        
        Args:
            order_id: ID заказа
            limit: Максимальное количество сообщений
            
        Returns:
            List[OrderMessage]: Список сообщений в хронологическом порядке
        """
        return self.db.query(OrderMessage)\
            .filter(OrderMessage.order_id == order_id)\
            .order_by(OrderMessage.sent_at.asc())\
            .limit(limit)\
            .all()
    
    def get_unread_user_messages_count(self, order_id: int) -> int:
        """
        Получить количество непрочитанных сообщений от пользователя
        (сообщения от пользователя, которые еще не просматривались в админке)
        
        Args:
            order_id: ID заказа
            
        Returns:
            int: Количество непрочитанных сообщений
        """
        # Пока считаем все сообщения от пользователя как "непрочитанные"
        # В будущем можно добавить поле "viewed_by_admin"
        return self.db.query(OrderMessage)\
            .filter(
                OrderMessage.order_id == order_id,
                OrderMessage.from_admin == False
            )\
            .count()
    
    def get_recent_user_messages(self, limit: int = 10) -> List[dict]:
        """
        Получить последние сообщения от пользователей по всем заказам
        
        Args:
            limit: Максимальное количество сообщений
            
        Returns:
            List[dict]: Список сообщений с информацией о заказе и пользователе
        """
        from sqlalchemy import desc
        
        messages = self.db.query(OrderMessage)\
            .filter(OrderMessage.from_admin == False)\
            .order_by(desc(OrderMessage.sent_at))\
            .limit(limit)\
            .all()
        
        result = []
        for message in messages:
            result.append({
                'message_id': message.id,
                'order_id': message.order_id,
                'order_topic': message.order.short_topic,
                'user_name': message.order.user.full_name,
                'user_username': message.order.user.username,
                'message_text': message.message_preview,
                'sent_at': message.sent_at,
                'delivered': message.delivered
            })
        
        return result