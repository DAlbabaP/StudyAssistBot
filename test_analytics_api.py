#!/usr/bin/env python3
"""
Тестирование API эндпоинтов аналитики
"""
import requests
import json
from pprint import pprint

# Базовый URL админ-панели
BASE_URL = "http://localhost:8000"

def test_endpoint(endpoint_path, description):
    """Тестирование отдельного эндпоинта"""
    url = f"{BASE_URL}{endpoint_path}"
    print(f"\n🔍 Тестирование: {description}")
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Статус: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ Данные получены:")
                pprint(data)
                return True
            except json.JSONDecodeError:
                print(f"❌ Ошибка парсинга JSON: {response.text[:200]}")
                return False
        else:
            print(f"❌ HTTP ошибка: {response.status_code}")
            print(f"Ответ: {response.text[:200]}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка запроса: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🚀 Тестирование API эндпоинтов аналитики")
    print("=" * 50)
    
    # Список эндпоинтов для тестирования
    endpoints = [
        ("/api/analytics/overview", "Общий обзор аналитики"),
        ("/api/analytics/orders/status", "Распределение заказов по статусам"),
        ("/api/analytics/orders/timeline?days=30", "Временная динамика заказов"),
        ("/api/analytics/revenue/timeline?days=30", "Временная динамика доходов"),
        ("/api/analytics/conversion/funnel", "Воронка конверсии"),
        ("/api/analytics/work-types", "Аналитика по типам работ"),
        ("/api/analytics/financial", "Финансовая аналитика"),
        ("/api/analytics/operational", "Операционные метрики"),
        ("/api/analytics/users", "Пользовательская аналитика"),
    ]
    
    success_count = 0
    
    for endpoint, description in endpoints:
        if test_endpoint(endpoint, description):
            success_count += 1
    
    print(f"\n📊 Результаты тестирования:")
    print(f"✅ Успешно: {success_count}/{len(endpoints)}")
    print(f"❌ Ошибок: {len(endpoints) - success_count}/{len(endpoints)}")
    
    if success_count == len(endpoints):
        print("🎉 Все эндпоинты работают!")
    else:
        print("⚠️  Некоторые эндпоинты не работают")

if __name__ == "__main__":
    main()
