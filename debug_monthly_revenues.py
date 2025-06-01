#!/usr/bin/env python3
"""
Скрипт для отладки месячных доходов
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.connection import SessionLocal
from app.database.models.payment import OrderPayment
from sqlalchemy import func, and_
from datetime import datetime, timedelta

def debug_monthly_revenues():
    """Отладка месячных доходов"""
    db = SessionLocal()
    try:
        print("=== ОТЛАДКА МЕСЯЧНЫХ ДОХОДОВ ===")
        
        # Проверим все платежи
        payments = db.query(OrderPayment).filter(OrderPayment.is_verified == True).all()
        print(f"Всего подтвержденных платежей: {len(payments)}")
        
        for payment in payments:
            print(f"  Платеж {payment.id}: {payment.amount} ₽, дата: {payment.created_at}")
            
        # Проверим группировку по месяцам напрямую
        print("\n=== ГРУППИРОВКА ПО МЕСЯЦАМ ===")
        monthly_revenues = db.query(
            func.strftime('%Y-%m', OrderPayment.created_at).label('month'),
            func.sum(OrderPayment.amount).label('revenue')
        ).filter(
            OrderPayment.is_verified == True
        ).group_by(
            func.strftime('%Y-%m', OrderPayment.created_at)
        ).order_by('month').all()
        
        print(f"Найдено месяцев с доходами: {len(monthly_revenues)}")
        for month, revenue in monthly_revenues:
            print(f"  {month}: {revenue} ₽")
            
        # Проверим текущий месяц
        print("\n=== ТЕКУЩИЙ МЕСЯЦ ===")
        current_month = datetime.now().replace(day=1)
        print(f"Начало текущего месяца: {current_month}")
        
        current_month_revenue = db.query(func.sum(OrderPayment.amount)).filter(
            and_(
                OrderPayment.is_verified == True,
                OrderPayment.created_at >= current_month
            )
        ).scalar() or 0
        print(f"Доход за текущий месяц: {current_month_revenue}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    debug_monthly_revenues()
