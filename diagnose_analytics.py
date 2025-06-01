#!/usr/bin/env python3
"""
Диагностика аналитики - проверка всех данных
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def diagnose_analytics():
    """Полная диагностика системы аналитики"""
    
    session = requests.Session()
    
    print("🔍 ДИАГНОСТИКА СИСТЕМЫ АНАЛИТИКИ")
    print("=" * 60)
    
    # Авторизация
    login_data = {"password": "admin123"}
    response = session.post(f"{BASE_URL}/login", data=login_data, allow_redirects=False)
    
    if response.status_code != 302:
        print("❌ Ошибка авторизации")
        return
    
    print("✅ Авторизация успешна")
    
    # Проверка всех endpoints
    endpoints = {
        "Общая статистика": "/api/analytics/overview",
        "Динамика заказов": "/api/analytics/orders/timeline",
        "Динамика доходов": "/api/analytics/revenue/timeline", 
        "Финансовая аналитика": "/api/analytics/financial",
        "Статусы заказов": "/api/analytics/orders/status",
        "Аналитика пользователей": "/api/analytics/users",
        "Операционные метрики": "/api/analytics/operational",
        "Статистика в реальном времени": "/api/analytics/realtime",
        "Воронка конверсий": "/api/analytics/conversion/funnel",
        "Типы работ": "/api/analytics/work-types"
    }
    
    all_working = True
    
    for name, endpoint in endpoints.items():
        print(f"\n📊 {name}")
        print(f"   Endpoint: {endpoint}")
        
        try:
            response = session.get(f"{BASE_URL}{endpoint}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # Анализ структуры данных
                    if isinstance(data, dict):
                        print(f"   ✅ Словарь с ключами: {list(data.keys())}")
                        
                        # Проверка наличия данных
                        has_meaningful_data = False
                        for key, value in data.items():
                            if isinstance(value, (int, float)) and value > 0:
                                has_meaningful_data = True
                                print(f"      📈 {key}: {value}")
                            elif isinstance(value, list) and len(value) > 0:
                                has_meaningful_data = True
                                print(f"      📋 {key}: список из {len(value)} элементов")
                            elif isinstance(value, dict) and len(value) > 0:
                                has_meaningful_data = True
                                print(f"      📊 {key}: объект с {len(value)} ключами")
                        
                        if not has_meaningful_data:
                            print("   ⚠️  Данные пустые или нулевые")
                            
                    elif isinstance(data, list):
                        print(f"   ✅ Массив из {len(data)} элементов")
                        if len(data) > 0:
                            print(f"      Пример элемента: {list(data[0].keys()) if isinstance(data[0], dict) else type(data[0])}")
                        else:
                            print("   ⚠️  Массив пустой")
                    else:
                        print(f"   ✅ Данные типа: {type(data)}")
                        
                except json.JSONDecodeError:
                    print(f"   ❌ Ошибка JSON: {response.text[:100]}...")
                    all_working = False
                    
            else:
                print(f"   ❌ HTTP {response.status_code}: {response.text[:100]}...")
                all_working = False
                
        except Exception as e:
            print(f"   ❌ Ошибка запроса: {e}")
            all_working = False
    
    print("\n" + "=" * 60)
    if all_working:
        print("🎉 ВСЕ ENDPOINTS РАБОТАЮТ! Проблема может быть в браузере или JavaScript.")
        print("\n💡 РЕКОМЕНДАЦИИ:")
        print("1. Откройте http://127.0.0.1:8000/analytics в браузере")
        print("2. Войдите с паролем: admin123")
        print("3. Откройте DevTools (F12) и проверьте Console на ошибки")
        print("4. Проверьте Network tab на failed запросы")
    else:
        print("❌ ОБНАРУЖЕНЫ ПРОБЛЕМЫ с некоторыми endpoints")
    
    print("🏁 Диагностика завершена")

if __name__ == "__main__":
    diagnose_analytics()
