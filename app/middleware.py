from fastapi import Request
from fastapi.responses import RedirectResponse
from .database import SessionLocal
from .models import User

def get_current_user(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    db.close()
    return user

def require_role(role: str):
    def role_checker(request: Request):
        user = get_current_user(request)
        if not user or user.role != role:
            return RedirectResponse("/login")
        return user
    return role_checker