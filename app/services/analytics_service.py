"""
Сервис аналитики и метрик для системы управления заказами
Предоставляет подробную статистику, бизнес-метрики и аналитику
"""
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract, case, text
from decimal import Decimal

from app.database.models.order import Order
from app.database.models.user import User
from app.database.models.payment import OrderPayment
from app.database.models.message import OrderMessage
from app.database.models.enums import OrderStatus


class AnalyticsService:
    """Сервис для расчета аналитики и метрик"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # === ОБЩАЯ СТАТИСТИКА ===
    
    def get_overview_stats(self) -> Dict[str, Any]:
        """Получить общий обзор статистики системы"""
        total_orders = self.db.query(Order).count()
        total_users = self.db.query(User).count()
        total_revenue = self.db.query(func.sum(OrderPayment.amount)).filter(
            OrderPayment.is_verified == True
        ).scalar() or 0
        
        avg_order_value = self.db.query(func.avg(Order.price)).filter(
            Order.price.isnot(None)
        ).scalar() or 0
        
        completion_rate = self._calculate_completion_rate()
        
        return {
            "total_orders": total_orders,
            "total_users": total_users,
            "total_revenue": float(total_revenue),
            "average_order_value": float(avg_order_value),
            "completion_rate": completion_rate,
            "last_updated": datetime.now().isoformat()
        }
    
    def get_orders_by_status(self) -> Dict[str, int]:
        """Получить распределение заказов по статусам"""
        status_counts = self.db.query(
            Order.status,
            func.count(Order.id)
        ).group_by(Order.status).all()
        
        result = {}
        for status, count in status_counts:
            result[status.value] = count
            
        # Добавляем статусы с нулевым количеством
        for status in OrderStatus:
            if status.value not in result:
                result[status.value] = 0
                
        return result
    
    # === ВРЕМЕННАЯ АНАЛИТИКА ===
    
    def get_orders_timeline(self, days: int = 30) -> List[Dict[str, Any]]:
        """Получить временную динамику заказов за указанный период"""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        orders_by_date = self.db.query(
            func.date(Order.created_at).label('date'),
            func.count(Order.id).label('count')
        ).filter(
            func.date(Order.created_at) >= start_date
        ).group_by(
            func.date(Order.created_at)
        ).order_by('date').all()
          # Создаем полный список дат с нулевыми значениями
        result = []
        current_date = start_date
        # Преобразуем строковые даты в объекты datetime.date для правильного поиска
        orders_dict = {}
        for date_str, count in orders_by_date:
            if isinstance(date_str, str):
                # Конвертируем строку в объект date
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                orders_dict[date_obj] = count
            else:
                orders_dict[date_str] = count
        
        while current_date <= end_date:
            result.append({
                "date": current_date.isoformat(),
                "orders_count": orders_dict.get(current_date, 0)
            })
            current_date += timedelta(days=1)
            
        return result
    
    def get_revenue_timeline(self, days: int = 30) -> List[Dict[str, Any]]:
        """Получить временную динамику доходов"""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Используем created_at для подтвержденных платежей, так как verified_at может быть NULL
        revenue_by_date = self.db.query(
            func.date(OrderPayment.created_at).label('date'),
            func.sum(OrderPayment.amount).label('revenue')
        ).filter(
            and_(
                OrderPayment.is_verified == True,
                func.date(OrderPayment.created_at) >= start_date
            )
        ).group_by(
            func.date(OrderPayment.created_at)
        ).order_by('date').all()
        result = []
        current_date = start_date
        # Преобразуем строковые даты в объекты datetime.date для правильного поиска
        revenue_dict = {}
        for date_str, revenue in revenue_by_date:
            if isinstance(date_str, str):
                # Конвертируем строку в объект date
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                revenue_dict[date_obj] = float(revenue)
            else:
                revenue_dict[date_str] = float(revenue)
        
        while current_date <= end_date:
            result.append({
                "date": current_date.isoformat(),
                "revenue": revenue_dict.get(current_date, 0.0)
            })
            current_date += timedelta(days=1)
            
        return result
    
    # === БИЗНЕС-МЕТРИКИ ===
    
    def get_conversion_funnel(self) -> Dict[str, Any]:
        """Получить воронку конверсии заказов"""
        total_orders = self.db.query(Order).count()
        
        # Статистика по этапам воронки
        funnel_stats = {}
        for status in OrderStatus:
            count = self.db.query(Order).filter(Order.status == status).count()
            funnel_stats[status.value] = {
                "count": count,
                "percentage": round((count / total_orders * 100) if total_orders > 0 else 0, 2)
            }
        
        # Конверсии между этапами
        new_orders = funnel_stats.get('new', {}).get('count', 0)
        in_progress = funnel_stats.get('in_progress', {}).get('count', 0)
        completed = funnel_stats.get('sent', {}).get('count', 0)
        
        return {
            "total_orders": total_orders,
            "funnel_stages": funnel_stats,
            "conversions": {
                "new_to_progress": round((in_progress / new_orders * 100) if new_orders > 0 else 0, 2),
                "progress_to_completed": round((completed / in_progress * 100) if in_progress > 0 else 0, 2),
                "overall_completion": round((completed / total_orders * 100) if total_orders > 0 else 0, 2)
            }
        }
    
    def get_work_type_analytics(self) -> List[Dict[str, Any]]:
        """Анализ по типам работ"""
        work_type_stats = self.db.query(
            Order.work_type,
            func.count(Order.id).label('count'),
            func.avg(Order.price).label('avg_price'),
            func.sum(case((Order.status == OrderStatus.SENT, 1), else_=0)).label('completed')
        ).filter(
            Order.price.isnot(None)
        ).group_by(Order.work_type).all()
        
        result = []
        for work_type, count, avg_price, completed in work_type_stats:
            completion_rate = round((completed / count * 100) if count > 0 else 0, 2)
            result.append({
                "work_type": work_type,
                "orders_count": count,
                "average_price": float(avg_price or 0),
                "completed_orders": completed,
                "completion_rate": completion_rate,
                "total_revenue": float((avg_price or 0) * completed)
            })
            
        return sorted(result, key=lambda x: x['orders_count'], reverse=True)
    
    def get_user_analytics(self) -> Dict[str, Any]:
        """Аналитика по пользователям"""
        total_users = self.db.query(User).count()
        
        # Пользователи с заказами
        users_with_orders = self.db.query(
            func.count(func.distinct(Order.user_id))
        ).scalar()
        
        # Активные пользователи (с заказами за последние 30 дней)
        month_ago = datetime.now() - timedelta(days=30)
        active_users = self.db.query(
            func.count(func.distinct(Order.user_id))
        ).filter(Order.created_at >= month_ago).scalar()
          # Топ пользователи по количеству заказов
        top_users = self.db.query(
            User.first_name,
            User.last_name,
            User.username,
            func.count(Order.id).label('orders_count'),
            func.sum(Order.price).label('total_spent')
        ).join(Order).group_by(User.id).order_by(
            func.count(Order.id).desc()
        ).limit(10).all()
        
        # Новые пользователи по дням (последние 7 дней)
        week_ago = datetime.now() - timedelta(days=7)
        new_users_daily = self.db.query(
            func.date(User.created_at).label('date'),
            func.count(User.id).label('count')
        ).filter(
            User.created_at >= week_ago
        ).group_by(
            func.date(User.created_at)
        ).order_by('date').all()
        
        return {
            "total_users": total_users,
            "users_with_orders": users_with_orders,
            "active_users_month": active_users,
            "conversion_rate": round((users_with_orders / total_users * 100) if total_users > 0 else 0, 2),            "top_users": [
                {
                    "name": f"{first_name or ''} {last_name or ''}".strip() or username or f"User {i+1}",
                    "username": username,
                    "orders_count": orders_count,
                    "total_spent": float(total_spent or 0)
                }
                for i, (first_name, last_name, username, orders_count, total_spent) in enumerate(top_users)
            ],            "new_users_daily": [
                {
                    "date": str(date),  # func.date() возвращает строку
                    "count": count
                }
                for date, count in new_users_daily
            ]
        }
    
    # === ФИНАНСОВАЯ АНАЛИТИКА ===
    
    def get_financial_analytics(self) -> Dict[str, Any]:
        """Финансовая аналитика"""
        # Общий доход
        total_revenue = self.db.query(func.sum(OrderPayment.amount)).filter(
            OrderPayment.is_verified == True
        ).scalar() or 0
        
        # Доход за текущий месяц - используем created_at вместо verified_at
        current_month = datetime.now().replace(day=1)
        monthly_revenue = self.db.query(func.sum(OrderPayment.amount)).filter(
            and_(
                OrderPayment.is_verified == True,
                OrderPayment.created_at >= current_month
            )
        ).scalar() or 0
        
        # Средний чек
        avg_payment = self.db.query(func.avg(OrderPayment.amount)).filter(
            OrderPayment.is_verified == True
        ).scalar() or 0
        
        # Статистика платежей
        total_payments = self.db.query(OrderPayment).count()
        verified_payments = self.db.query(OrderPayment).filter(
            OrderPayment.is_verified == True
        ).count()
        rejected_payments = self.db.query(OrderPayment).filter(
            OrderPayment.is_rejected == True
        ).count()
        pending_payments = self.db.query(OrderPayment).filter(
            and_(
                OrderPayment.is_verified == False,
                OrderPayment.is_rejected == False
            )
        ).count()
          # Доходы по месяцам (последние 12 месяцев) - используем created_at
        monthly_revenues = []
        current_date = datetime.now()
        
        for i in range(12):
            # Правильно вычисляем начало месяца
            if i == 0:
                month_start = current_date.replace(day=1)
            else:
                # Идем назад по месяцам
                year = current_date.year
                month = current_date.month - i
                if month <= 0:
                    month += 12
                    year -= 1
                month_start = datetime(year, month, 1)
            
            # Начало следующего месяца
            next_month = month_start.month + 1
            next_year = month_start.year
            if next_month > 12:
                next_month = 1
                next_year += 1
            month_end = datetime(next_year, next_month, 1)
            
            month_revenue = self.db.query(func.sum(OrderPayment.amount)).filter(
                and_(
                    OrderPayment.is_verified == True,
                    OrderPayment.created_at >= month_start,
                    OrderPayment.created_at < month_end
                )
            ).scalar() or 0
            
            monthly_revenues.append({
                "month": month_start.strftime("%Y-%m"),
                "revenue": float(month_revenue)
            })
        
        monthly_revenues.reverse()
        
        return {
            "total_revenue": float(total_revenue),
            "monthly_revenue": float(monthly_revenue),
            "average_payment": float(avg_payment),
            "payment_stats": {
                "total": total_payments,
                "verified": verified_payments,
                "rejected": rejected_payments,
                "pending": pending_payments,
                "verification_rate": round((verified_payments / total_payments * 100) if total_payments > 0 else 0, 2)
            },
            "monthly_revenues": monthly_revenues
        }
    
    # === ОПЕРАЦИОННАЯ АНАЛИТИКА ===
    
    def get_operational_metrics(self) -> Dict[str, Any]:
        """Операционные метрики"""
        # Среднее время выполнения заказа
        completed_orders = self.db.query(Order).filter(
            Order.status == OrderStatus.SENT
        ).all()
        
        if completed_orders:
            total_time = sum([
                (order.updated_at - order.created_at).total_seconds() / 3600  # в часах
                for order in completed_orders
            ])
            avg_completion_time = total_time / len(completed_orders)
        else:
            avg_completion_time = 0
        
        # Статистика сообщений
        total_messages = self.db.query(OrderMessage).count()
        admin_messages = self.db.query(OrderMessage).filter(
            OrderMessage.from_admin == True
        ).count()
        user_messages = self.db.query(OrderMessage).filter(
            OrderMessage.from_admin == False
        ).count()
        
        # Активность по дням недели
        weekday_stats = self.db.query(
            extract('dow', Order.created_at).label('weekday'),
            func.count(Order.id).label('count')
        ).group_by('weekday').all()
        
        weekdays = ['Воскресенье', 'Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота']
        weekday_activity = []
        for dow, count in weekday_stats:
            weekday_activity.append({
                "day": weekdays[int(dow)],
                "orders": count
            })
        
        # Активность по часам
        hourly_stats = self.db.query(
            extract('hour', Order.created_at).label('hour'),
            func.count(Order.id).label('count')
        ).group_by('hour').order_by('hour').all()
        
        return {
            "avg_completion_time_hours": round(avg_completion_time, 2),
            "message_stats": {
                "total": total_messages,
                "from_admin": admin_messages,
                "from_users": user_messages,
                "admin_ratio": round((admin_messages / total_messages * 100) if total_messages > 0 else 0, 2)
            },
            "weekday_activity": weekday_activity,
            "hourly_activity": [
                {
                    "hour": int(hour),
                    "orders": count
                }
                for hour, count in hourly_stats
            ]
        }
    
    # === ЭКСПОРТ ДАННЫХ ===
    
    def get_export_data(self, start_date: Optional[datetime] = None, 
                       end_date: Optional[datetime] = None) -> Dict[str, List[Dict]]:
        """Получить данные для экспорта"""
        query = self.db.query(Order).join(User)
        
        if start_date:
            query = query.filter(Order.created_at >= start_date)
        if end_date:
            query = query.filter(Order.created_at <= end_date)
            
        orders = query.order_by(Order.created_at.desc()).all()
        
        export_orders = []
        for order in orders:
            export_orders.append({
                "id": order.id,
                "client_name": order.user.full_name,
                "client_username": order.user.username,
                "work_type": order.work_type,
                "subject": order.subject,
                "topic": order.topic,
                "volume": order.volume,
                "deadline": order.deadline,
                "status": order.status.value,
                "price": float(order.price) if order.price else None,
                "created_at": order.created_at.isoformat(),
                "updated_at": order.updated_at.isoformat(),
                "messages_count": order.messages_count,
                "files_count": order.files_count
            })
        
        # Экспорт платежей
        payments_query = self.db.query(OrderPayment).join(Order).join(User)
        if start_date:
            payments_query = payments_query.filter(OrderPayment.created_at >= start_date)
        if end_date:
            payments_query = payments_query.filter(OrderPayment.created_at <= end_date)
            
        payments = payments_query.order_by(OrderPayment.created_at.desc()).all()
        
        export_payments = []
        for payment in payments:
            export_payments.append({
                "id": payment.id,
                "order_id": payment.order_id,
                "client_name": payment.order.user.full_name,
                "amount": float(payment.amount),
                "status": payment.status_text,
                "is_verified": payment.is_verified,
                "is_rejected": payment.is_rejected,
                "created_at": payment.created_at.isoformat(),
                "verified_at": payment.verified_at.isoformat() if payment.verified_at else None
            })
        
        return {
            "orders": export_orders,
            "payments": export_payments
        }
    
    # === ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ===
    
    def _calculate_completion_rate(self) -> float:
        """Рассчитать процент завершенных заказов"""
        total_orders = self.db.query(Order).count()
        if total_orders == 0:
            return 0.0
            
        completed_orders = self.db.query(Order).filter(
            Order.status == OrderStatus.SENT
        ).count()
        
        return round((completed_orders / total_orders * 100), 2)
    
    def get_real_time_stats(self) -> Dict[str, Any]:
        """Получить статистику в реальном времени для дашборда"""
        today = datetime.now().date()
        
        # Заказы сегодня
        orders_today = self.db.query(Order).filter(
            func.date(Order.created_at) == today
        ).count()
        
        # Новые сообщения (непрочитанные от пользователей)
        new_messages = self.db.query(OrderMessage).filter(
            and_(
                OrderMessage.from_admin == False,
                OrderMessage.delivered == False
            )
        ).count()
        
        # Платежи на проверке
        pending_payments = self.db.query(OrderPayment).filter(
            and_(
                OrderPayment.is_verified == False,
                OrderPayment.is_rejected == False
            )
        ).count()
        
        # Активные заказы
        active_orders = self.db.query(Order).filter(
            Order.status.in_([OrderStatus.NEW, OrderStatus.IN_PROGRESS])
        ).count()
        
        return {
            "orders_today": orders_today,
            "new_messages": new_messages,
            "pending_payments": pending_payments,
            "active_orders": active_orders,
            "timestamp": datetime.now().isoformat()
        }
