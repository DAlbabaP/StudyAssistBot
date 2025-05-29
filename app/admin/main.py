from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from typing import Optional
import os

from fastapi import UploadFile, File, BackgroundTasks
from app.services.communication_service import CommunicationService
import aiofiles
import uuid
from pathlib import Path


from app.config import settings
from app.database.connection import get_db
from app.services.user_service import UserService
from app.services.order_service import OrderService
from app.database.models import OrderStatus


from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

# Создание приложения FastAPI
app = FastAPI(title="Telegram Bot Admin Panel")

# Добавление middleware для сессий
app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)


def create_app():
    """Создание экземпляра FastAPI приложения для тестирования"""
    return app


# Подключение статических файлов и шаблонов
app.mount("/static", StaticFiles(directory="app/admin/static"), name="static")
templates = Jinja2Templates(directory="app/admin/templates")


# Простая авторизация (в реальном проекте используйте более надежную)
def verify_admin(request: Request):
    """Проверка авторизации администратора"""
    admin_session = request.session.get("admin_authenticated")
    if not admin_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется авторизация"
        )


@app.get("/", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    """Страница входа в админ-панель"""
    if request.session.get("admin_authenticated"):
        return RedirectResponse("/dashboard", status_code=302)
    
    return templates.TemplateResponse(
        "login.html", 
        {"request": request}
    )


@app.post("/login")
async def admin_login(
    request: Request,
    password: str = Form(...),
):
    """Обработка входа в админ-панель"""
    # Простая проверка пароля (замените на более надежную)
    if password == "admin123":  # Поменяйте на ваш пароль
        request.session["admin_authenticated"] = True
        return RedirectResponse("/dashboard", status_code=302)
    
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request, 
            "error": "Неверный пароль"
        }
    )


@app.get("/logout")
async def admin_logout(request: Request):
    """Выход из админ-панели"""
    request.session.clear()
    return RedirectResponse("/", status_code=302)


@app.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    db: Session = Depends(get_db)
):
    """Главная страница админ-панели"""
    verify_admin(request)
    
    user_service = UserService(db)
    order_service = OrderService(db)
    
    # Получаем статистику
    stats = order_service.get_orders_statistics()
    users_count = user_service.get_users_count()
    
    # Получаем последние заказы
    recent_orders = order_service.get_orders_by_status(page=1, per_page=5)
    
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "stats": stats,
            "users_count": users_count,
            "recent_orders": recent_orders['orders']
        }
    )

@app.get("/admin/recent_messages")
async def get_recent_user_messages(
    request: Request,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """API для получения последних сообщений от пользователей"""
    verify_admin(request)
    
    communication_service = CommunicationService(db)
    recent_messages = communication_service.get_recent_user_messages(limit)
    
    return {
        "messages_count": len(recent_messages),
        "messages": recent_messages
    }


@app.get("/orders/{order_id}/unread_count")
async def get_unread_messages_count(
    request: Request,
    order_id: int,
    db: Session = Depends(get_db)
):
    """API для получения количества непрочитанных сообщений от пользователя"""
    verify_admin(request)
    
    communication_service = CommunicationService(db)
    unread_count = communication_service.get_unread_user_messages_count(order_id)
    
    return {
        "order_id": order_id,
        "unread_count": unread_count
    }


@app.get("/orders", response_class=HTMLResponse)
async def admin_orders(
    request: Request,
    page: int = 1,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Страница управления заказами"""
    verify_admin(request)
    
    order_service = OrderService(db)
    
    # Определяем статус для фильтра
    status = None
    if status_filter and status_filter != "all":
        try:
            status = OrderStatus(status_filter)
        except ValueError:
            status = None
    
    # Получаем заказы
    result = order_service.get_orders_by_status(status, page=page, per_page=10)
    
    return templates.TemplateResponse(
        "orders.html",
        {
            "request": request,
            "orders": result['orders'],
            "pagination": result,
            "current_filter": status_filter or "all",
            "statuses": list(OrderStatus)
        }
    )


@app.get("/orders/{order_id}", response_class=HTMLResponse)
async def admin_order_detail(
    request: Request,
    order_id: int,
    db: Session = Depends(get_db)
):
    """Детальная страница заказа"""
    verify_admin(request)
    
    order_service = OrderService(db)
    order = order_service.get_order_by_id(order_id)
    
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    
    # 🔥 ИСПРАВЛЕНО: Явно загружаем файлы заказа
    print(f"🔍 Загружаем детали заказа #{order_id}")
    
    # Способ 1: Через relationship (должен работать автоматически)
    files_via_relationship = order.files
    print(f"   Файлов через relationship: {len(files_via_relationship)}")
    
    # Способ 2: Через сервис (для надежности)
    files_via_service = order_service.get_order_files(order_id)
    print(f"   Файлов через сервис: {len(files_via_service)}")
    
    # Способ 3: Прямой запрос (для отладки)
    from app.database.models.file import OrderFile
    files_direct = db.query(OrderFile).filter(OrderFile.order_id == order_id).all()
    print(f"   Файлов прямым запросом: {len(files_direct)}")
    
    # Используем файлы из прямого запроса для надежности
    order.files = files_direct
    
    # Добавляем отладочную информацию
    if files_direct:
        print("   📎 Найденные файлы:")
        for file in files_direct:
            print(f"      • ID: {file.id}, Имя: {file.filename}")
            print(f"        Путь: {file.file_path}")
            print(f"        Размер: {file.file_size}")
            print(f"        Существует: {os.path.exists(file.file_path) if file.file_path else False}")
    else:
        print("   📎 Файлов не найдено")
    
    return templates.TemplateResponse(
        "order_detail.html",
        {
            "request": request,
            "order": order,
            "statuses": list(OrderStatus)
        }
    )


@app.post("/orders/{order_id}/status")
async def update_order_status(
    request: Request,
    order_id: int,
    new_status: str = Form(...),
    db: Session = Depends(get_db)
):
    """Обновление статуса заказа"""
    verify_admin(request)
    
    order_service = OrderService(db)
    communication_service = CommunicationService(db)
    
    try:
        status = OrderStatus(new_status)
        success = order_service.update_order_status(order_id, status, "Изменено через веб-панель")
        
        if success:
            # Если статус изменен на "ожидает оплаты", отправляем реквизиты
            if status == OrderStatus.WAITING_PAYMENT:
                from app.services.payment_service import PaymentService
                payment_service = PaymentService(db)
                
                try:
                    payment_message = payment_service.create_payment_request(order_id)
                    await communication_service.send_message_to_user(
                        order_id, 
                        payment_message, 
                        from_admin=True
                    )
                except Exception as e:
                    print(f"❌ Ошибка отправки реквизитов: {e}")
            
            return RedirectResponse(f"/orders/{order_id}?success=status_updated", status_code=302)
        else:
            raise HTTPException(status_code=400, detail="Ошибка обновления статуса")
    
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный статус")


@app.post("/orders/{order_id}/price")
async def update_order_price(
    request: Request,
    order_id: int,
    price: float = Form(...),
    db: Session = Depends(get_db)
):
    """Обновление цены заказа"""
    verify_admin(request)
    
    try:
        order_service = OrderService(db)
        
        # Валидация цены
        if price <= 0:
            raise HTTPException(status_code=400, detail="Цена должна быть положительным числом")
        
        if price > 1000000:  # Максимальная цена 1 млн рублей
            raise HTTPException(status_code=400, detail="Цена слишком большая")
        
        # Проверяем существование заказа
        order = order_service.get_order_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Заказ не найден")
        
        # Обновляем цену
        success = order_service.update_order_price(order_id, price)
        
        if success:
            return RedirectResponse(f"/orders/{order_id}?success=price_updated", status_code=302)
        else:
            raise HTTPException(status_code=400, detail="Ошибка обновления цены")
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Неверное значение цены: {str(e)}")
    except Exception as e:
        print(f"Error updating price: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@app.get("/users", response_class=HTMLResponse)
async def admin_users(
    request: Request,
    page: int = 1,
    db: Session = Depends(get_db)
):
    """Страница управления пользователями"""
    verify_admin(request)
    
    user_service = UserService(db)
    users = user_service.get_all_users(include_blocked=True)
    
    # Простая пагинация
    per_page = 20
    total = len(users)
    start = (page - 1) * per_page
    end = start + per_page
    users_page = users[start:end]
    
    total_pages = (total + per_page - 1) // per_page
    
    return templates.TemplateResponse(
        "users.html",
        {
            "request": request,
            "users": users_page,
            "pagination": {
                "page": page,
                "total_pages": total_pages,
                "total": total
            }
        }
    )

@app.get("/admin/dashboard_stats")
async def get_dashboard_stats(
    request: Request,
    db: Session = Depends(get_db)
):
    """Расширенная статистика для дашборда с информацией о сообщениях"""
    verify_admin(request)
    
    user_service = UserService(db)
    order_service = OrderService(db)
    communication_service = CommunicationService(db)
    
    # Получаем обычную статистику
    stats = order_service.get_orders_statistics()
    users_count = user_service.get_users_count()
    
    # Добавляем статистику по сообщениям
    from app.database.models.message import OrderMessage
    
    total_messages = db.query(OrderMessage).count()
    user_messages = db.query(OrderMessage).filter(OrderMessage.from_admin == False).count()
    admin_messages = db.query(OrderMessage).filter(OrderMessage.from_admin == True).count()
    
    # Последние сообщения от пользователей
    recent_user_messages = communication_service.get_recent_user_messages(5)
    
    return {
        "orders": stats,
        "users_count": users_count,
        "messages": {
            "total_messages": total_messages,
            "user_messages": user_messages,
            "admin_messages": admin_messages,
            "recent_user_messages": recent_user_messages
        }
    }


@app.api_route("/files/download/{file_id}", methods=["GET", "HEAD"])
async def download_file(
    request: Request,
    file_id: int,
    db: Session = Depends(get_db)
):
    """Скачивание файла заказа с поддержкой HEAD запросов для проверки"""
    verify_admin(request)
    
    # Получаем информацию о файле из базы данных
    from app.database.models.file import OrderFile
    
    file_record = db.query(OrderFile).filter(OrderFile.id == file_id).first()
    
    if not file_record:
        print(f"❌ Файл с ID {file_id} не найден в БД")
        raise HTTPException(status_code=404, detail="Файл не найден")
    
    print(f"📁 Запрос на {'проверку' if request.method == 'HEAD' else 'скачивание'} файла: {file_record.filename}")
    print(f"   Путь: {file_record.file_path}")
    
    # Проверяем существование файла на диске
    file_path = file_record.file_path
    if not file_path or not os.path.exists(file_path):
        print(f"❌ Файл не найден на диске: {file_path}")
        raise HTTPException(status_code=404, detail="Файл не найден на диске")
    
    print(f"✅ {'Проверяем' if request.method == 'HEAD' else 'Отправляем'} файл: {file_record.filename}")
    
    # Возвращаем файл с оригинальным именем из БД
    return FileResponse(
        path=file_path,
        filename=file_record.filename,  # Оригинальное имя из БД
        media_type='application/octet-stream'
    )


@app.get("/orders/{order_id}/files")
async def get_order_files(
    request: Request,
    order_id: int,
    db: Session = Depends(get_db)
):
    """API для получения списка файлов заказа"""
    verify_admin(request)
    
    order_service = OrderService(db)
    
    # Проверяем существование заказа
    order = order_service.get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    
    # Получаем файлы
    files = order_service.get_order_files(order_id)
    
    print(f"📁 API запрос файлов для заказа #{order_id}: найдено {len(files)} файлов")
    
    return {
        "order_id": order_id,
        "files_count": len(files),
        "files": [
            {
                "id": file.id,
                "filename": file.filename,  # Оригинальное имя
                "file_size": file.file_size,
                "file_type": file.file_type,
                "uploaded_at": file.uploaded_at.isoformat(),
                "download_url": f"/files/download/{file.id}",
                "exists_on_disk": os.path.exists(file.file_path) if file.file_path else False,
                "file_path_on_disk": os.path.basename(file.file_path) if file.file_path else None  # Только имя файла на диске
            }
            for file in files
        ]
    }
@app.get("/orders/{order_id}/dialog")
async def get_order_dialog(
    request: Request,
    order_id: int,
    db: Session = Depends(get_db)
):
    """API для получения полного диалога по заказу (админ + пользователь)"""
    verify_admin(request)
    
    communication_service = CommunicationService(db)
    messages = communication_service.get_dialog_messages(order_id, limit=100)
    
    # Получаем информацию о заказе
    order_service = OrderService(db)
    order = order_service.get_order_by_id(order_id)
    
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    
    return {
        "order_id": order_id,
        "order_info": {
            "id": order.id,
            "work_type": order.work_type,
            "topic": order.short_topic,
            "status": order.status.value,
            "user_name": order.user.full_name,
            "user_username": order.user.username
        },
        "messages_count": len(messages),
        "messages": [
            {
                "id": msg.id,
                "text": msg.message_text,
                "from_admin": msg.from_admin,
                "sender": msg.sender_label,
                "sent_at": msg.sent_at.isoformat(),
                "delivered": msg.delivered,
                "telegram_message_id": msg.telegram_message_id
            }
            for msg in messages
        ]
    }


@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request, exc):
    """Обработчик HTTP ошибок"""
    if exc.status_code == 404:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error_code": 404,
                "error_message": "Страница не найдена"
            },
            status_code=404
        )
    elif exc.status_code == 401:
        return RedirectResponse("/", status_code=302)
    else:
        return await http_exception_handler(request, exc)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """Обработчик ошибок валидации"""
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "error_code": 400,
            "error_message": "Неверные данные запроса"
        },
        status_code=400
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Общий обработчик ошибок"""
    import traceback
    print(f"Unexpected error: {exc}")
    print(traceback.format_exc())
    
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "error_code": 500,
            "error_message": "Внутренняя ошибка сервера"
        },
        status_code=500
    )

@app.get("/debug/files/{order_id}")
async def debug_order_files(
    request: Request,
    order_id: int,
    db: Session = Depends(get_db)
):
    """Отладочный эндпоинт для файлов заказа"""
    verify_admin(request)
    
    from app.database.models.file import OrderFile
    
    # Прямой запрос файлов
    files = db.query(OrderFile).filter(OrderFile.order_id == order_id).all()
    
    debug_info = {
        "order_id": order_id,
        "files_count": len(files),
        "files": []
    }
    
    for file in files:
        file_exists = os.path.exists(file.file_path) if file.file_path else False
        disk_filename = os.path.basename(file.file_path) if file.file_path else None
        
        debug_info["files"].append({
            "id": file.id,
            "db_filename": file.filename,  # Имя в БД (оригинальное)
            "disk_filename": disk_filename,  # Имя файла на диске
            "file_path": file.file_path,
            "file_size": file.file_size,
            "uploaded_at": str(file.uploaded_at),
            "exists_on_disk": file_exists,
            "disk_size": os.path.getsize(file.file_path) if file_exists else None,
            "size_match": os.path.getsize(file.file_path) == file.file_size if file_exists and file.file_size else None
        })
    
    return debug_info

@app.post("/orders/{order_id}/send_message")
async def send_message_to_user(
    request: Request,
    order_id: int,
    background_tasks: BackgroundTasks,
    message: str = Form(...),
    db: Session = Depends(get_db)
):
    """Отправить сообщение пользователю"""
    verify_admin(request)
    
    if not message or not message.strip():
        raise HTTPException(status_code=400, detail="Сообщение не может быть пустым")
    
    # Проверяем существование заказа
    order_service = OrderService(db)
    order = order_service.get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    
    # Отправляем сообщение в фоне
    communication_service = CommunicationService(db)
    
    async def send_message_background():
        try:
            success = await communication_service.send_message_to_user(
                order_id=order_id,
                message_text=message.strip(),
                from_admin=True
            )
            if success:
                print(f"✅ Сообщение успешно отправлено пользователю по заказу #{order_id}")
            else:
                print(f"❌ Не удалось отправить сообщение по заказу #{order_id}")
        except Exception as e:
            print(f"❌ Ошибка отправки сообщения: {e}")
    
    background_tasks.add_task(send_message_background)
    
    return RedirectResponse(f"/orders/{order_id}?success=message_sent", status_code=302)


@app.post("/orders/{order_id}/upload_file")
async def upload_admin_file(
    request: Request,
    order_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Загрузить файл от админа для заказа"""
    verify_admin(request)
    
    # Проверяем существование заказа
    order_service = OrderService(db)
    order = order_service.get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    
    # Проверяем файл
    if not file.filename:
        raise HTTPException(status_code=400, detail="Файл должен иметь имя")
    
    if file.size > settings.max_file_size:
        raise HTTPException(
            status_code=413, 
            detail=f"Файл слишком большой. Максимум: {settings.max_file_size / 1024 / 1024:.1f} МБ"
        )
    
    try:
        # Создаем директорию для файлов админа
        admin_files_dir = Path(settings.upload_path) / str(order_id) / "admin"
        admin_files_dir.mkdir(parents=True, exist_ok=True)
        
        # Генерируем уникальное имя файла (чтобы избежать конфликтов)
        file_extension = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4().hex[:8]}_{file.filename}"
        file_path = admin_files_dir / unique_filename
        
        # Сохраняем файл
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Сохраняем в БД
        communication_service = CommunicationService(db)
        order_file = communication_service.save_admin_file(
            order_id=order_id,
            file_path=str(file_path),
            original_filename=file.filename,
            file_size=file.size
        )
        
        print(f"✅ Файл от админа загружен: {file.filename} для заказа #{order_id}")
        
        return RedirectResponse(f"/orders/{order_id}?success=file_uploaded", status_code=302)
        
    except Exception as e:
        print(f"❌ Ошибка загрузки файла: {e}")
        raise HTTPException(status_code=500, detail="Ошибка загрузки файла")


@app.post("/orders/{order_id}/send_file/{file_id}")
async def send_file_to_user(
    request: Request,
    order_id: int,
    file_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Отправить файл пользователю через Telegram"""
    verify_admin(request)
    
    # Проверяем существование заказа и файла
    order_service = OrderService(db)
    order = order_service.get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    
    from app.database.models.file import OrderFile
    file_record = db.query(OrderFile).filter(
        OrderFile.id == file_id,
        OrderFile.order_id == order_id
    ).first()
    
    if not file_record:
        raise HTTPException(status_code=404, detail="Файл не найден")
    
    # Отправляем файл в фоне
    communication_service = CommunicationService(db)
    
    async def send_file_background():
        try:
            success = await communication_service.send_file_to_user(order_id, file_id)
            if success:
                print(f"✅ Файл {file_record.filename} успешно отправлен пользователю")
            else:
                print(f"❌ Не удалось отправить файл {file_record.filename}")
        except Exception as e:
            print(f"❌ Ошибка отправки файла: {e}")
    
    background_tasks.add_task(send_file_background)
    
    return RedirectResponse(f"/orders/{order_id}?success=file_sent", status_code=302)


@app.get("/orders/{order_id}/messages")
async def get_order_messages(
    request: Request,
    order_id: int,
    db: Session = Depends(get_db)
):
    """API для получения сообщений по заказу"""
    verify_admin(request)
    
    communication_service = CommunicationService(db)
    messages = communication_service.get_order_messages(order_id)
    
    return {
        "order_id": order_id,
        "messages_count": len(messages),
        "messages": [
            {
                "id": msg.id,
                "text": msg.message_text,
                "from_admin": msg.from_admin,
                "sender": msg.sender_label,
                "sent_at": msg.sent_at.isoformat(),
                "delivered": msg.delivered,
                "preview": msg.message_preview
            }
            for msg in messages
        ]
    }


@app.get("/orders/{order_id}/admin_files")
async def get_admin_files(
    request: Request,
    order_id: int,
    db: Session = Depends(get_db)
):
    """API для получения файлов загруженных админом"""
    verify_admin(request)
    
    from app.database.models.file import OrderFile
    
    admin_files = db.query(OrderFile).filter(
        OrderFile.order_id == order_id,
        OrderFile.uploaded_by_admin == True
    ).all()
    
    return {
        "order_id": order_id,
        "admin_files_count": len(admin_files),
        "files": [
            {
                "id": file.id,
                "filename": file.filename,
                "file_size": file.file_size,
                "uploaded_at": file.uploaded_at.isoformat(),
                "sent_to_user": file.sent_to_user,
                "sent_at": file.sent_at.isoformat() if file.sent_at else None,
                "exists_on_disk": os.path.exists(file.file_path) if file.file_path else False
            }
            for file in admin_files        ]
    }


# === ПЛАТЕЖИ ===

@app.get("/orders/{order_id}/payments")
async def get_order_payments(
    request: Request,
    order_id: int,
    db: Session = Depends(get_db)
):
    """Получить платежи по заказу"""
    verify_admin(request)
    
    from app.services.payment_service import PaymentService
    payment_service = PaymentService(db)
    
    payments = payment_service.get_order_payments(order_id)
    
    return {
        "order_id": order_id,
        "payments_count": len(payments),
        "payments": [
            {
                "id": payment.id,
                "amount": float(payment.amount),
                "amount_text": payment.amount_rub,
                "status": payment.status_text,
                "is_verified": payment.is_verified,
                "is_rejected": payment.is_rejected,
                "screenshot_file_id": payment.screenshot_file_id,
                "screenshot_message": payment.screenshot_message,
                "created_at": payment.created_at.isoformat(),
                "verified_at": payment.verified_at.isoformat() if payment.verified_at else None,
                "rejected_at": payment.rejected_at.isoformat() if payment.rejected_at else None
            }
            for payment in payments
        ]
    }


@app.post("/payments/{payment_id}/verify")
async def verify_payment(
    request: Request,
    payment_id: int,
    db: Session = Depends(get_db)
):
    """Подтвердить платеж"""
    verify_admin(request)
    
    from app.services.payment_service import PaymentService
    payment_service = PaymentService(db)
    
    success = payment_service.verify_payment(payment_id, request.session.get("admin_user_id", 1))
    
    if success:
        return {"success": True, "message": "Платеж подтвержден"}
    else:
        raise HTTPException(status_code=400, detail="Ошибка подтверждения платежа")


@app.post("/payments/{payment_id}/reject")
async def reject_payment(
    request: Request,
    payment_id: int,
    reason: str = Form(...),
    db: Session = Depends(get_db)
):
    """Отклонить платеж"""
    verify_admin(request)
    
    from app.services.payment_service import PaymentService
    payment_service = PaymentService(db)
    
    success = payment_service.reject_payment(payment_id, reason, request.session.get("admin_user_id", 1))
    
    if success:
        return {"success": True, "message": "Платеж отклонен"}
    else:
        raise HTTPException(status_code=400, detail="Ошибка отклонения платежа")


@app.get("/admin/pending_payments")
async def get_pending_payments(
    request: Request,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Получить платежи на проверке"""
    verify_admin(request)
    
    from app.services.payment_service import PaymentService
    payment_service = PaymentService(db)
    
    payments = payment_service.get_pending_payments(limit)
    
    return {
        "pending_count": len(payments),
        "payments": [
            {
                "id": payment.id,
                "order_id": payment.order_id,
                "order_topic": payment.order.short_topic,
                "amount": float(payment.amount),
                "amount_text": payment.amount_rub,
                "user_name": payment.order.user.full_name,
                "screenshot_file_id": payment.screenshot_file_id,
                "screenshot_message": payment.screenshot_message,
                "created_at": payment.created_at.isoformat()
            }
            for payment in payments
        ]
    }


# === ОТЛАДОЧНЫЕ ЭНДПОИНТЫ ===

@app.get("/debug/payments/{order_id}")
async def debug_payments(
    order_id: int,
    db: Session = Depends(get_db)
):
    """Отладочный эндпоинт для платежей БЕЗ проверки авторизации"""
    try:
        from app.services.payment_service import PaymentService
        payment_service = PaymentService(db)
        
        payments = payment_service.get_order_payments(order_id)
        
        result = {
            "order_id": order_id,
            "payments_count": len(payments),
            "debug": True,
            "payments": []
        }
        
        for payment in payments:
            result["payments"].append({
                "id": payment.id,
                "amount": float(payment.amount),
                "amount_text": payment.amount_rub,
                "status": payment.status_text,
                "is_verified": payment.is_verified,
                "is_rejected": payment.is_rejected,
                "screenshot_file_id": payment.screenshot_file_id,
                "screenshot_message": payment.screenshot_message,
                "created_at": payment.created_at.isoformat(),
                "verified_at": payment.verified_at.isoformat() if payment.verified_at else None,
                "rejected_at": payment.rejected_at.isoformat() if payment.rejected_at else None
            })
        
        return result
        
    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc(),
            "order_id": order_id
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.admin_host, port=settings.admin_port)


