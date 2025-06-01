#!/usr/bin/env python3
"""
Тест API аналитики с аутентификацией
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_analytics_with_auth():
    """Тестирование API аналитики с авторизацией"""
    
    # Создаем сессию для сохранения cookies
    session = requests.Session()
    
    print("🔐 Тестирование авторизации и API аналитики...")
    print("=" * 60)
    
    # 1. Попытка доступа без авторизации
    print("\n1. Проверка доступа без авторизации:")
    try:
        response = session.get(f"{BASE_URL}/api/analytics/overview")
        print(f"   Статус: {response.status_code}")
        if response.status_code == 401:
            print("   ✅ Правильно заблокирован доступ без авторизации")
        else:
            print("   ❌ Неожиданный статус ответа")
    except Exception as e:
        print(f"   ❌ Ошибка запроса: {e}")
    
    # 2. Авторизация
    print("\n2. Выполнение авторизации:")
    try:
        login_data = {"password": "admin123"}
        response = session.post(f"{BASE_URL}/login", data=login_data, allow_redirects=False)
        print(f"   Статус: {response.status_code}")
        
        if response.status_code == 302:
            print("   ✅ Авторизация успешна (перенаправление)")
        else:
            print("   ❌ Ошибка авторизации")
            return
            
    except Exception as e:
        print(f"   ❌ Ошибка авторизации: {e}")
        return
      # 3. Тестирование API endpoints после авторизации
    endpoints = [
        "/api/analytics/overview",
        "/api/analytics/orders/timeline", 
        "/api/analytics/revenue/timeline",
        "/api/analytics/financial",
        "/api/analytics/orders/status",
        "/api/analytics/users",
        "/api/analytics/operational",
        "/api/analytics/realtime"
    ]
    
    print("\n3. Тестирование API endpoints:")
    for endpoint in endpoints:
        print(f"\n   Тестирую: {endpoint}")
        try:
            response = session.get(f"{BASE_URL}{endpoint}")
            print(f"   Статус: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   ✅ Получены данные: {type(data)} размером {len(str(data))} символов")
                    
                    # Показываем структуру данных
                    if isinstance(data, dict):
                        print(f"   📋 Ключи: {list(data.keys())}")
                        
                        # Проверяем наличие данных
                        has_data = False
                        for key, value in data.items():
                            if isinstance(value, (list, dict)) and len(value) > 0:
                                has_data = True
                            elif isinstance(value, (int, float)) and value > 0:
                                has_data = True
                                
                        if has_data:
                            print("   ✅ Содержит данные для отображения")
                        else:
                            print("   ⚠️  Данные пустые или нулевые")
                    
                except Exception as e:
                    print(f"   ❌ Ошибка парсинга JSON: {e}")
                    print(f"   Содержимое: {response.text[:200]}...")
                    
            elif response.status_code == 401:
                print("   ❌ Требуется авторизация (сессия не сохранилась)")
            else:
                print(f"   ❌ Ошибка: {response.status_code}")
                if response.text:
                    print(f"   Ответ: {response.text[:200]}...")
                    
        except Exception as e:
            print(f"   ❌ Ошибка запроса: {e}")
    
    print("\n" + "=" * 60)
    print("🏁 Тестирование завершено")

if __name__ == "__main__":
    test_analytics_with_auth()
