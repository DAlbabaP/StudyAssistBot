#!/usr/bin/env python3
"""
Детальная диагностика логики временной шкалы аналитики
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from sqlalchemy import func
from app.database.connection import get_db_session
from app.database.models.order import Order
from app.services.analytics_service import AnalyticsService

def debug_timeline_logic():
    """Диагностируем логику временной шкалы"""
    print("🔍 ДИАГНОСТИКА ЛОГИКИ ВРЕМЕННОЙ ШКАЛЫ")
    print("=" * 60)
    
    with get_db_session() as db:
        service = AnalyticsService(db)
        
        # Текущая дата и период
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        
        print(f"📅 Период анализа:")
        print(f"   Начало: {start_date}")
        print(f"   Конец: {end_date}")
        print(f"   Сегодня: {datetime.now()}")
        
        # Проверяем SQL запрос
        print(f"\n🔎 SQL запрос для заказов:")
        orders_by_date = db.query(
            func.date(Order.created_at).label('date'),
            func.count(Order.id).label('count')
        ).filter(
            func.date(Order.created_at) >= start_date
        ).group_by(
            func.date(Order.created_at)
        ).order_by('date').all()
        
        print(f"   Найдено записей: {len(orders_by_date)}")
        for date, count in orders_by_date:
            print(f"   {date}: {count} заказов")
        
        # Проверяем все заказы в период
        print(f"\n📋 Все заказы в период {start_date} - {end_date}:")
        all_orders = db.query(Order).filter(
            func.date(Order.created_at) >= start_date
        ).order_by(Order.created_at).all()
        
        print(f"   Всего заказов в периоде: {len(all_orders)}")
        for order in all_orders[:10]:  # Показываем первые 10
            print(f"   ID {order.id}: {order.created_at.date()} ({order.created_at})")
        
        # Тестируем логику создания полного списка
        print(f"\n🔧 Тестируем логику создания временной шкалы:")
        orders_dict = {date: count for date, count in orders_by_date}
        print(f"   orders_dict: {orders_dict}")
        
        result = []
        current_date = start_date
        days_processed = 0
        
        while current_date <= end_date and days_processed < 5:  # Показываем первые 5 дней
            count = orders_dict.get(current_date, 0)
            result.append({
                "date": current_date.isoformat(),
                "orders_count": count
            })
            print(f"   {current_date}: {count} заказов")
            current_date += timedelta(days=1)
            days_processed += 1
        
        print("   ...")
        
        # Получаем результат от сервиса
        print(f"\n📊 Результат от AnalyticsService.get_orders_timeline():")
        timeline = service.get_orders_timeline(30)
        print(f"   Количество дней: {len(timeline)}")
        
        # Показываем дни с ненулевыми значениями
        non_zero_days = [day for day in timeline if day['orders_count'] > 0]
        print(f"   Дни с заказами: {len(non_zero_days)}")
        for day in non_zero_days:
            print(f"   {day['date']}: {day['orders_count']} заказов")
        
        # Показываем последние 5 дней
        print(f"\n📈 Последние 5 дней:")
        for day in timeline[-5:]:
            print(f"   {day['date']}: {day['orders_count']} заказов")

if __name__ == "__main__":
    debug_timeline_logic()
