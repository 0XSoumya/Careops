from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Contact, Conversation, Booking, Inventory
from app.middleware import get_current_user
from app.utils.security import hash_password

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


# ======================================
# OWNER DASHBOARD
# ======================================

@router.get("/owner", response_class=HTMLResponse)
def owner_dashboard(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request)
    if not user or user.role != "owner":
        return RedirectResponse("/login", status_code=302)

    # Core Metrics
    total_leads = db.query(Contact).count()

    active_conversations = db.query(Conversation).filter(
        Conversation.status == "open"
    ).count()

    pending_bookings = db.query(Booking).filter(
        Booking.status == "pending"
    ).count()

    confirmed_bookings = db.query(Booking).filter(
        Booking.status == "confirmed"
    ).count()

    completed_bookings = db.query(Booking).filter(
        Booking.status == "completed"
    ).count()

    # Inventory Metrics
    items = db.query(Inventory).all()
    total_inventory = len(items)
    low_stock = len([i for i in items if i.quantity <= i.threshold])
    healthy_stock = total_inventory - low_stock

    return templates.TemplateResponse(
        "owner_dashboard.html",
        {
            "request": request,
            "user": user,
            "total_leads": total_leads,
            "active_conversations": active_conversations,
            "pending_bookings": pending_bookings,
            "confirmed_bookings": confirmed_bookings,
            "completed_bookings": completed_bookings,
            "low_stock": low_stock,
            "healthy_stock": healthy_stock,
            "total_inventory": total_inventory
        }
    )


# ======================================
# STAFF MANAGEMENT
# ======================================

@router.get("/owner/staff", response_class=HTMLResponse)
def manage_staff(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request)
    if not user or user.role != "owner":
        return RedirectResponse("/login", status_code=302)

    staff_members = db.query(User).filter(User.role == "staff").all()

    return templates.TemplateResponse(
        "owner_staff.html",
        {
            "request": request,
            "user": user,
            "staff_members": staff_members
        }
    )


@router.post("/owner/staff/add")
def add_staff(
    request: Request,
    name: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = get_current_user(request)
    if not user or user.role != "owner":
        return RedirectResponse("/login", status_code=302)

    new_staff = User(
        name=name,
        username=username,
        password_hash=hash_password(password),
        role="staff",
        is_active=True
    )

    db.add(new_staff)
    db.commit()

    return RedirectResponse("/owner/staff", status_code=302)


# ======================================
# INVENTORY MANAGEMENT
# ======================================

@router.get("/owner/inventory", response_class=HTMLResponse)
def owner_inventory(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request)
    if not user or user.role != "owner":
        return RedirectResponse("/login", status_code=302)

    items = db.query(Inventory).all()

    return templates.TemplateResponse(
        "owner_inventory.html",
        {
            "request": request,
            "user": user,
            "items": items
        }
    )


@router.post("/owner/inventory/update")
def update_inventory(
    request: Request,
    item_id: int = Form(...),
    quantity: int = Form(...),
    db: Session = Depends(get_db)
):
    user = get_current_user(request)
    if not user or user.role != "owner":
        return RedirectResponse("/login", status_code=302)

    item = db.query(Inventory).filter(
        Inventory.id == item_id
    ).first()

    if item:
        item.quantity = quantity
        db.commit()

    return RedirectResponse("/owner/inventory", status_code=302)


@router.post("/owner/inventory/add")
def add_inventory(
    request: Request,
    name: str = Form(...),
    quantity: int = Form(...),
    threshold: int = Form(...),
    db: Session = Depends(get_db)
):
    user = get_current_user(request)
    if not user or user.role != "owner":
        return RedirectResponse("/login", status_code=302)

    new_item = Inventory(
        name=name,
        quantity=quantity,
        threshold=threshold
    )

    db.add(new_item)
    db.commit()

    return RedirectResponse("/owner/inventory", status_code=302)
