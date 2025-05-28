from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from typing import Optional
import os

from app.config import settings
from app.database.connection import get_db
from app.services.user_service import UserService
from app.services.order_service import OrderService
from app.database.models import OrderStatus

from fastapi import HTTPException
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
    
    try:
        status = OrderStatus(new_status)
        success = order_service.update_order_status(order_id, status, "Изменено через веб-панель")
        
        if success:
            return RedirectResponse(f"/orders/{order_id}?success=status_updated", status_code=302)
        else:
            raise HTTPException(status_code=400, detail="Ошибка обновления статуса")
    
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный статус")
    
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


@app.get("/files/download/{file_id}")
async def download_file(
    request: Request,
    file_id: int,
    db: Session = Depends(get_db)
):
    """Скачивание файла заказа"""
    verify_admin(request)
    
    # Получаем информацию о файле из базы данных
    from app.database.models.file import OrderFile
    
    file_record = db.query(OrderFile).filter(OrderFile.id == file_id).first()
    
    if not file_record:
        print(f"❌ Файл с ID {file_id} не найден в БД")
        raise HTTPException(status_code=404, detail="Файл не найден")
    
    print(f"📁 Запрос на скачивание файла: {file_record.filename}")
    print(f"   Путь: {file_record.file_path}")
    
    # Проверяем существование файла на диске
    file_path = file_record.file_path
    if not file_path or not os.path.exists(file_path):
        print(f"❌ Файл не найден на диске: {file_path}")
        raise HTTPException(status_code=404, detail="Файл не найден на диске")
    
    print(f"✅ Отправляем файл: {file_record.filename}")
    
    # Возвращаем файл для скачивания
    return FileResponse(
        path=file_path,
        filename=file_record.filename,
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
                "filename": file.filename,
                "file_size": file.file_size,
                "file_type": file.file_type,
                "uploaded_at": file.uploaded_at.isoformat(),
                "download_url": f"/files/download/{file.id}",
                "exists_on_disk": os.path.exists(file.file_path) if file.file_path else False
            }
            for file in files
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
        debug_info["files"].append({
            "id": file.id,
            "filename": file.filename,
            "file_path": file.file_path,
            "file_size": file.file_size,
            "uploaded_at": str(file.uploaded_at),
            "exists_on_disk": file_exists,
            "disk_size": os.path.getsize(file.file_path) if file_exists else None
        })
    
    return debug_info


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.admin_host, port=settings.admin_port)


