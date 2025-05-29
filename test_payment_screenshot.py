#!/usr/bin/env python3
"""
Тестирование скриншотов платежей
"""

from app.database.connection import get_db_session
from app.services.payment_service import PaymentService
from app.services.order_service import OrderService

def test_payment_with_screenshot():
    """Тест добавления скриншота к платежу"""
    
    db = get_db_session()
    try:
        payment_service = PaymentService(db)
        order_service = OrderService(db)
        
        print("🧪 Тестирование скриншотов платежей")
        print("=" * 50)
        
        # Получаем первый платеж
        payments = payment_service.get_order_payments(16)  # Заказ #16 из прошлого теста
        if not payments:
            print("❌ Платежи не найдены")
            return
        
        payment = payments[0]
        print(f"💳 Работаем с платежом #{payment.id}")
        print(f"   Сумма: {payment.amount_rub}")
        print(f"   Статус: {payment.status_text}")
        
        # Добавляем фиктивный файл для теста
        fake_file_id = 1  # Предполагаем, что файл с ID 1 существует
        user_message = "Вот мой чек об оплате"
        
        print(f"\n🔄 Добавление скриншота к платежу...")
        success = payment_service.process_payment_screenshot(
            order_id=16,
            file_id=fake_file_id,
            user_message=user_message
        )
        
        if success:
            print("✅ Скриншот добавлен успешно")
        else:
            print("❌ Ошибка добавления скриншота")
            return
        
        # Проверяем обновленные платежи
        print(f"\n🔍 Проверка обновленных платежей...")
        updated_payments = payment_service.get_order_payments(16)
        for payment in updated_payments:
            print(f"   💳 Платеж #{payment.id}")
            print(f"      Скриншот: {'Есть' if payment.screenshot_file_id else 'Нет'}")
            print(f"      Сообщение: {payment.screenshot_message or 'Нет'}")
        
        # Проверяем платежи на проверке
        print(f"\n🔍 Платежи на проверке (с скриншотами):")
        pending_payments = payment_service.get_pending_payments(10)
        print(f"✅ Найдено: {len(pending_payments)}")
        
        for payment in pending_payments:
            print(f"   ⏳ Платеж #{payment.id} (заказ #{payment.order_id})")
            print(f"      Сумма: {payment.amount_rub}")
            print(f"      Пользователь: {payment.order.user.full_name}")
            if payment.screenshot_message:
                print(f"      Сообщение: {payment.screenshot_message}")
        
        # Тестируем подтверждение платежа
        if pending_payments:
            payment_to_verify = pending_payments[0]
            print(f"\n🔄 Тестируем подтверждение платежа #{payment_to_verify.id}...")
            
            success = payment_service.verify_payment(payment_to_verify.id, admin_user_id=1)
            if success:
                print("✅ Платеж подтвержден успешно")
                
                # Проверяем статус заказа
                updated_order = order_service.get_order_by_id(payment_to_verify.order_id)
                print(f"   Статус заказа изменен на: {updated_order.status}")
            else:
                print("❌ Ошибка подтверждения платежа")
        
        print("\n✅ Тестирование завершено!")
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_payment_with_screenshot()
