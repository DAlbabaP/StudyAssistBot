"""
Тесты для моделей базы данных
"""
import pytest
from datetime import datetime
from app.database.models import User, Order
from app.database.models.enums import OrderStatus, WorkType


def test_user_creation():
    """Тест создания пользователя"""
    user = User(
        telegram_id=123456789,
        username="testuser",
        first_name="Test",
        last_name="User",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    assert user.telegram_id == 123456789
    assert user.username == "testuser"
    assert user.first_name == "Test"
    assert user.last_name == "User"
    assert user.is_admin is False
    assert user.is_active is True


def test_order_creation():
    """Тест создания заказа"""
    order = Order(
        title="Тестовый реферат",
        description="Описание тестового реферата",
        work_type="essay",
        subject="Информатика",
        pages_count=10,
        status=OrderStatus.NEW,
        user_id=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    assert order.title == "Тестовый реферат"
    assert order.work_type == "essay"
    assert order.status == OrderStatus.NEW
    assert order.pages_count == 10


def test_order_status_enum():
    """Тест enum статусов"""
    assert OrderStatus.NEW == "new"
    assert OrderStatus.IN_PROGRESS == "in_progress"
    assert OrderStatus.READY == "ready"
    assert OrderStatus.SENT == "sent"


def test_work_type_enum():
    """Тест enum типов работ"""
    assert WorkType.ESSAY == "essay"
    assert WorkType.COURSEWORK == "coursework"
    assert WorkType.DIPLOMA == "diploma"
