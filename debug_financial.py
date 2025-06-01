#!/usr/bin/env python3
"""
Скрипт для отладки финансовой аналитики
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.connection import SessionLocal
from app.services.analytics_service import AnalyticsService

def debug_financial_analytics():
    """Отладка финансовой аналитики"""
    db = SessionLocal()
    try:
        analytics_service = AnalyticsService(db)
        
        print("=== ОТЛАДКА ФИНАНСОВОЙ АНАЛИТИКИ ===")
        
        # Получаем финансовую аналитику
        financial_data = analytics_service.get_financial_analytics()
        
        print(f"Общий доход: {financial_data['total_revenue']}")
        print(f"Доход за месяц: {financial_data['monthly_revenue']}")
        print(f"Средний платеж: {financial_data['average_payment']}")
        print(f"Статистика платежей: {financial_data['payment_stats']}")
        print(f"Месячные доходы ({len(financial_data['monthly_revenues'])} месяцев):")
        
        for month_data in financial_data['monthly_revenues']:
            print(f"  {month_data['month']}: {month_data['revenue']} ₽")
            
        print("\n=== РЕЗУЛЬТАТ ===")
        if financial_data['total_revenue'] > 0:
            print("✅ Финансовая аналитика возвращает данные")
        else:
            print("❌ Финансовая аналитика возвращает нулевые значения")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    debug_financial_analytics()
