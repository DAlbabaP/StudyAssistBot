"""
API роуты для админ-панели
"""
from fastapi import APIRouter, HTTPException, Depends, File, UploadFile
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
from datetime import datetime

from app.database.connection import get_db
from app.services.order_service import OrderService
from app.services.user_service import UserService
from app.database.models.enums import OrderStatus
from app.config import settings

router = APIRouter()


@router.get("/orders/{order_id}")
async def get_order(order_id: int, db: Session = Depends(get_db)):
    """Получить заказ по ID"""
    order_service = OrderService(db)
    order = await order_service.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    
    return {
        "id": order.id,
        "title": order.title,
        "description": order.description,
        "work_type": order.work_type,
        "subject": order.subject,
        "deadline": order.deadline.isoformat() if order.deadline else None,
        "pages_count": order.pages_count,
        "price": float(order.price) if order.price else None,
        "status": order.status.value,
        "admin_notes": order.admin_notes,
        "created_at": order.created_at.isoformat(),
        "updated_at": order.updated_at.isoformat(),
        "user": {
            "id": order.user.id,
            "telegram_id": order.user.telegram_id,
            "username": order.user.username,
            "first_name": order.user.first_name,
            "last_name": order.user.last_name
        }
    }


@router.post("/orders/{order_id}/status")
async def change_order_status(
    order_id: int, 
    status_data: dict,
    db: Session = Depends(get_db)
):
    """Изменить статус заказа"""
    try:
        new_status = OrderStatus(status_data["status"])
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный статус")
    
    order_service = OrderService(db)
    order = await order_service.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    
    await order_service.update_status(
        order_id, 
        new_status, 
        status_data.get("comment", "")
    )
    
    return {"message": "Статус успешно изменен"}


@router.post("/orders/{order_id}/price")
async def set_order_price(
    order_id: int,
    price_data: dict,
    db: Session = Depends(get_db)
):
    """Установить цену заказа"""
    try:
        price = float(price_data["price"])
        if price < 0:
            raise ValueError("Цена не может быть отрицательной")
    except (ValueError, KeyError):
        raise HTTPException(status_code=400, detail="Неверная цена")
    
    order_service = OrderService(db)
    order = await order_service.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    
    await order_service.set_price(order_id, price)
    
    return {"message": "Цена успешно установлена"}


@router.post("/orders/{order_id}/files")
async def upload_files(
    order_id: int,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """Загрузить файлы к заказу"""
    order_service = OrderService(db)
    order = await order_service.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    
    uploaded_files = []
    
    for file in files:
        # Проверка размера файла
        if file.size > settings.max_file_size:
            raise HTTPException(
                status_code=413, 
                detail=f"Файл {file.filename} слишком большой"
            )
        
        # Создание директории для заказа
        order_dir = os.path.join(settings.upload_path, str(order_id))
        os.makedirs(order_dir, exist_ok=True)
        
        # Генерация уникального имени файла
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{file.filename}"
        file_path = os.path.join(order_dir, filename)
        
        # Сохранение файла
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Добавление записи в БД
        await order_service.add_file(
            order_id=order_id,
            filename=filename,
            original_filename=file.filename,
            file_path=file_path,
            file_size=file.size,
            mime_type=file.content_type,
            uploaded_by_admin=True
        )
        
        uploaded_files.append({
            "filename": filename,
            "original_filename": file.filename,
            "size": file.size
        })
    
    return {
        "message": f"Загружено файлов: {len(uploaded_files)}",
        "files": uploaded_files
    }


@router.get("/files/{file_id}/download")
async def download_file(file_id: int, db: Session = Depends(get_db)):
    """Скачать файл"""
    order_service = OrderService(db)
    file_record = await order_service.get_file(file_id)
    
    if not file_record:
        raise HTTPException(status_code=404, detail="Файл не найден")
    
    if not os.path.exists(file_record.file_path):
        raise HTTPException(status_code=404, detail="Файл не найден на диске")
    
    from fastapi.responses import FileResponse
    return FileResponse(
        path=file_record.file_path,
        filename=file_record.original_filename,
        media_type=file_record.mime_type or 'application/octet-stream'
    )


@router.delete("/files/{file_id}")
async def delete_file(file_id: int, db: Session = Depends(get_db)):
    """Удалить файл"""
    order_service = OrderService(db)
    file_record = await order_service.get_file(file_id)
    
    if not file_record:
        raise HTTPException(status_code=404, detail="Файл не найден")
    
    # Удаление файла с диска
    if os.path.exists(file_record.file_path):
        os.remove(file_record.file_path)
    
    # Удаление записи из БД
    await order_service.delete_file(file_id)
    
    return {"message": "Файл успешно удален"}


@router.delete("/orders/{order_id}")
async def delete_order(order_id: int, db: Session = Depends(get_db)):
    """Удалить заказ"""
    order_service = OrderService(db)
    order = await order_service.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    
    # Удаление файлов заказа
    order_dir = os.path.join(settings.upload_path, str(order_id))
    if os.path.exists(order_dir):
        shutil.rmtree(order_dir)
    
    # Удаление заказа из БД
    await order_service.delete_order(order_id)
    
    return {"message": "Заказ успешно удален"}


@router.get("/statistics")
async def get_statistics(db: Session = Depends(get_db)):
    """Получить статистику"""
    order_service = OrderService(db)
    user_service = UserService(db)
    
    stats = await order_service.get_statistics()
    user_stats = await user_service.get_statistics()
    
    return {
        "orders": stats,
        "users": user_stats
    }
