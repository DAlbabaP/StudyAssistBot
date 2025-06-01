"""
Функции авторизации для админ-панели
"""
from fastapi import HTTPException, Request, status


def verify_admin(request: Request):
    """Проверка авторизации администратора для HTML страниц"""
    admin_session = request.session.get("admin_authenticated")
    if not admin_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется авторизация"
        )


def verify_admin_api(request: Request):
    """Проверка авторизации администратора для API эндпоинтов"""
    admin_session = request.session.get("admin_authenticated")
    if not admin_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется авторизация для доступа к API"
        )
    return True
