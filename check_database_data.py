#!/usr/bin/env python3
"""
Диагностика данных в базе - проверка дат заказов
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database.connection import get_db
from app.database.models.order import Order
from app.database.models.user import User
from datetime import datetime, timedelta

def check_database_data():
    """Проверка данных в базе данных"""
    
    print("🔍 ДИАГНОСТИКА ДАННЫХ В БАЗЕ")
    print("=" * 60)
    
    # Получаем сессию базы данных
    db = next(get_db())
    
    try:
        # 1. Общая статистика
        total_orders = db.query(Order).count()
        total_users = db.query(User).count()
        
        print(f"📊 Общая статистика:")
        print(f"   Всего заказов: {total_orders}")
        print(f"   Всего пользователей: {total_users}")
        
        if total_orders == 0:
            print("❌ В базе нет заказов!")
            return
        
        # 2. Даты заказов
        print(f"\n📅 Анализ дат заказов:")
        
        # Первый и последний заказ
        first_order = db.query(Order).order_by(Order.created_at.asc()).first()
        last_order = db.query(Order).order_by(Order.created_at.desc()).first()
        
        if first_order and last_order:
            print(f"   Первый заказ: {first_order.created_at} (ID: {first_order.id})")
            print(f"   Последний заказ: {last_order.created_at} (ID: {last_order.id})")
            
            # Разница во времени
            time_diff = last_order.created_at - first_order.created_at
            print(f"   Временной диапазон: {time_diff.days} дней")
        
        # 3. Заказы по дням
        print(f"\n📈 Заказы по дням (последние 10 дней):")
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=10)
        
        orders_by_date = db.query(
            func.date(Order.created_at).label('date'),
            func.count(Order.id).label('count')
        ).filter(
            func.date(Order.created_at) >= start_date
        ).group_by(
            func.date(Order.created_at)
        ).order_by('date').all()
        
        if orders_by_date:
            for date, count in orders_by_date:
                print(f"   {date}: {count} заказов")
        else:
            print("   ❌ Нет заказов за последние 10 дней")
            
        # 4. Все заказы с датами
        print(f"\n📋 Все заказы в базе:")
        all_orders = db.query(Order.id, Order.created_at, Order.status, Order.price).order_by(Order.created_at.desc()).limit(20).all()
        
        for order in all_orders:
            price_str = f"{order.price}₽" if order.price else "не указана"
            print(f"   ID {order.id}: {order.created_at} | {order.status.value} | {price_str}")
        
        # 5. Проверка текущей даты и времени
        current_time = datetime.now()
        print(f"\n🕒 Текущая дата и время: {current_time}")
        print(f"   Дата: {current_time.date()}")
        print(f"   Время: {current_time.time()}")
        
        # 6. Проверка фильтра временной динамики
        print(f"\n🔎 Проверка логики get_orders_timeline:")
        days = 60
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        print(f"   Период: {start_date} - {end_date}")
        print(f"   Количество дней: {days}")
        
        # Проверяем заказы в этом диапазоне
        orders_in_range = db.query(Order).filter(
            func.date(Order.created_at) >= start_date
        ).count()
        
        print(f"   Заказов в диапазоне: {orders_in_range}")
        
        if orders_in_range == 0:
            print("   ❌ Все заказы находятся ВНЕ временного диапазона!")
            print("   💡 Это объясняет, почему график показывает нули")
        
    finally:
        db.close()

if __name__ == "__main__":
    check_database_data()
