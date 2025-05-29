#!/usr/bin/env python3
"""
Тестирование системы платежей
"""

from app.database.connection import get_db_session
from app.services.payment_service import PaymentService
from app.services.order_service import OrderService

def test_payments():
    """Тест создания и обработки платежей"""
    
    db = get_db_session()
    try:
        payment_service = PaymentService(db)
        order_service = OrderService(db)
        
        print("🧪 Тестирование системы платежей")
        print("=" * 50)
        
        # Находим заказ для тестирования
        orders = order_service.get_orders_by_status(page=1, per_page=5)
        if not orders['orders']:
            print("❌ Нет заказов для тестирования")
            return
        
        order = orders['orders'][0]
        print(f"📋 Тестируем с заказом #{order.id}")
        print(f"   Тема: {order.topic}")
        print(f"   Цена: {order.price} руб" if order.price else "   Цена: не установлена")
        
        # Устанавливаем цену если её нет
        if not order.price:
            order_service.update_order_price(order.id, 1500.0)
            print("💰 Установлена тестовая цена: 1500 руб")
        
        # Создаём платежный запрос
        print("\n🔄 Создание платежного запроса...")
        try:
            message = payment_service.create_payment_request(order.id)
            print("✅ Платежный запрос создан успешно")
            print(f"📄 Сообщение: {message[:200]}...")
        except Exception as e:
            print(f"❌ Ошибка создания платежного запроса: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # Проверяем платежи по заказу
        print(f"\n🔍 Получение платежей для заказа #{order.id}...")
        payments = payment_service.get_order_payments(order.id)
        print(f"✅ Найдено платежей: {len(payments)}")
        
        for payment in payments:
            print(f"   💳 Платеж #{payment.id}")
            print(f"      Сумма: {payment.amount_rub}")
            print(f"      Статус: {payment.status_text}")
            print(f"      Создан: {payment.created_at}")
            if payment.screenshot_file_id:
                print(f"      Скриншот: файл #{payment.screenshot_file_id}")
        
        # Проверяем платежи на проверке
        print(f"\n🔍 Проверка платежей на рассмотрении...")
        pending_payments = payment_service.get_pending_payments(10)
        print(f"✅ Платежей на проверке: {len(pending_payments)}")
        
        if pending_payments:
            for payment in pending_payments:
                print(f"   ⏳ Платеж #{payment.id} (заказ #{payment.order_id})")
                print(f"      Сумма: {payment.amount_rub}")
                print(f"      Пользователь: {payment.order.user.full_name}")
        
        print("\n✅ Тестирование завершено успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_payments()
