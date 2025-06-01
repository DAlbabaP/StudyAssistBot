#!/usr/bin/env python3
"""
Скрипт для проверки данных в базе данных
"""

from app.database.connection import get_db
from app.database.models import Order, OrderPayment, OrderStatus
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

def check_database_data():
    """Проверяем данные в базе данных"""
    # Получаем сессию базы данных
    db = next(get_db())
    
    try:
        # Проверяем заказы за последние дни
        recent_orders = db.query(Order).filter(
            Order.created_at >= datetime.now() - timedelta(days=7)
        ).all()
        
        print('=== ЗАКАЗЫ ЗА ПОСЛЕДНИЕ 7 ДНЕЙ ===')
        for order in recent_orders:
            print(f'Заказ {order.id}: статус={order.status}, цена={order.price}, создан={order.created_at}')
          # Проверяем платежи
        payments = db.query(OrderPayment).filter(
            OrderPayment.created_at >= datetime.now() - timedelta(days=7)
        ).all()
        
        print('\n=== ПЛАТЕЖИ ЗА ПОСЛЕДНИЕ 7 ДНЕЙ ===')
        for payment in payments:
            status = "✅ Подтвержден" if payment.is_verified else ("❌ Отклонен" if payment.is_rejected else "⏳ На проверке")
            print(f'Платеж {payment.id}: заказ={payment.order_id}, сумма={payment.amount}, статус={status}, создан={payment.created_at}')
          # Проверяем завершенные заказы (статус SENT)
        completed_orders = db.query(Order).filter(
            Order.status == OrderStatus.SENT,
            Order.created_at >= datetime.now() - timedelta(days=7)
        ).all()
        
        print('\n=== ЗАВЕРШЕННЫЕ ЗАКАЗЫ (СТАТУС SENT) ЗА ПОСЛЕДНИЕ 7 ДНЕЙ ===')
        for order in completed_orders:
            print(f'Заказ {order.id}: цена={order.price}, создан={order.created_at}')
            
        # Проверяем подтвержденные платежи с verified_at
        verified_payments = db.query(OrderPayment).filter(
            OrderPayment.is_verified == True,
            OrderPayment.verified_at.isnot(None)
        ).all()
        
        print('\n=== ПОДТВЕРЖДЕННЫЕ ПЛАТЕЖИ С VERIFIED_AT ===')
        for payment in verified_payments:
            print(f'Платеж {payment.id}: заказ={payment.order_id}, сумма={payment.amount}, verified_at={payment.verified_at}')
            
        # Проверяем все заказы в базе
        all_orders = db.query(Order).all()
        print(f'\n=== ВСЕГО ЗАКАЗОВ В БАЗЕ: {len(all_orders)} ===')
          # Проверяем все платежи в базе
        all_payments = db.query(OrderPayment).all()
        print(f'=== ВСЕГО ПЛАТЕЖЕЙ В БАЗЕ: {len(all_payments)} ===')
        
    finally:
        db.close()

if __name__ == "__main__":
    check_database_data()
