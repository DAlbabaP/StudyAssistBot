#!/usr/bin/env python3
"""
Тестирование API платежей
"""

import requests
import json

def test_payments_api():
    """Тестирование API платежей"""
    
    # Базовый URL админ-панели
    base_url = "http://127.0.0.1:8000"
    
    print("🧪 Тестирование API платежей")
    print("=" * 50)
    
    # Тестируем получение платежей для заказа
    order_id = 16  # Заказ из наших тестов
    
    try:
        print(f"🔍 Запрос платежей для заказа #{order_id}...")
        
        # Сначала тестируем отладочный эндпоинт без авторизации
        response = requests.get(f"{base_url}/debug/payments/{order_id}")
        
        print(f"📡 Статус ответа: {response.status_code}")
        print(f"📄 Content-Type: {response.headers.get('content-type', 'N/A')}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ Данные получены успешно")
                print(f"📊 Количество платежей: {data.get('payments_count', 0)}")
                
                if data.get('debug'):
                    print("🔧 Отладочный режим активен")
                
                if data.get('error'):
                    print(f"❌ Ошибка на сервере: {data['error']}")
                    if data.get('traceback'):
                        print(f"📄 Traceback:\n{data['traceback']}")
                
                if data.get('payments'):
                    for payment in data['payments']:
                        print(f"   💳 Платеж #{payment['id']}: {payment['amount_text']}")
                        print(f"      Статус: {payment['status']}")
                        print(f"      Скриншот: {'Есть' if payment['screenshot_file_id'] else 'Нет'}")
                else:
                    print("   Платежей не найдено")
                    
            except json.JSONDecodeError as e:
                print(f"❌ Не удалось распарсить JSON: {e}")
                print(f"📄 Ответ: {response.text[:200]}...")
                
        elif response.status_code == 401:
            print("❌ Ошибка авторизации (401)")
            print("💡 Нужно авторизоваться в админ-панели")
            
        elif response.status_code == 404:
            print("❌ Endpoint не найден (404)")
            print("💡 Проверьте правильность URL")
            
        else:
            print(f"❌ Ошибка HTTP {response.status_code}")
            print(f"📄 Ответ: {response.text[:200]}...")
            
    except requests.exceptions.ConnectionError:
        print("❌ Не удается подключиться к серверу")
        print("💡 Убедитесь, что админ-панель запущена (python main_admin.py)")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    test_payments_api()
