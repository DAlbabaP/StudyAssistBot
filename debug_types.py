#!/usr/bin/env python3
"""
Детальная диагностика типов данных в запросе
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from sqlalchemy import func
from app.database.connection import get_db_session
from app.database.models.order import Order

def debug_data_types():
    """Диагностируем типы данных в SQL запросе"""
    print("🔍 ДИАГНОСТИКА ТИПОВ ДАННЫХ")
    print("=" * 50)
    
    with get_db_session() as db:
        # Текущая дата и период
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        
        print(f"📅 Типы дат:")
        print(f"   start_date: {start_date} (тип: {type(start_date)})")
        print(f"   end_date: {end_date} (тип: {type(end_date)})")
        
        # Проверяем что возвращает SQL
        orders_by_date = db.query(
            func.date(Order.created_at).label('date'),
            func.count(Order.id).label('count')
        ).filter(
            func.date(Order.created_at) >= start_date
        ).group_by(
            func.date(Order.created_at)
        ).order_by('date').all()
        
        print(f"\n🔎 Результат SQL запроса:")
        print(f"   Количество записей: {len(orders_by_date)}")
        
        for i, (date, count) in enumerate(orders_by_date):
            print(f"   {i+1}. date: {date} (тип: {type(date)}) | count: {count}")
        
        # Создаем словарь как в оригинальном коде
        orders_dict = {date: count for date, count in orders_by_date}
        print(f"\n📋 Словарь orders_dict:")
        for key, value in orders_dict.items():
            print(f"   {key} (тип: {type(key)}): {value}")
        
        # Тестируем поиск
        print(f"\n🔧 Тестируем поиск:")
        test_date = datetime(2025, 5, 28).date()
        print(f"   Ищем дату: {test_date} (тип: {type(test_date)})")
        print(f"   Найдено: {orders_dict.get(test_date, 'НЕ НАЙДЕНО')}")
        
        # Проверяем все ключи
        print(f"\n🔍 Сравниваем ключи:")
        for key in orders_dict.keys():
            print(f"   {key} == {test_date}: {key == test_date}")
            print(f"   str({key}) == str({test_date}): {str(key) == str(test_date)}")

if __name__ == "__main__":
    debug_data_types()
