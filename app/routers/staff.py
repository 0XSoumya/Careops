from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Conversation, Message, Booking, Inventory
from app.middleware import get_current_user
from app.services.whatsapp_service import send_whatsapp_message

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


# =========================
# STAFF DASHBOARD
# =========================

@router.get("/staff", response_class=HTMLResponse)
def staff_dashboard(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request)
    if not user or user.role != "staff":
        return RedirectResponse("/login", status_code=302)

    open_conversations = db.query(Conversation).filter(
        Conversation.status == "open"
    ).count()

    confirmed_bookings = db.query(Booking).filter(
        Booking.status == "confirmed"
    ).count()

    inventory_items = db.query(Inventory).all()

    return templates.TemplateResponse(
        "staff_dashboard.html",
        {
            "request": request,
            "user": user,
            "open_conversations": open_conversations,
            "confirmed_bookings": confirmed_bookings,
            "inventory_items": inventory_items
        }
    )


# =========================
# STAFF INBOX
# =========================

@router.get("/staff/inbox", response_class=HTMLResponse)
def staff_inbox(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request)
    if not user or user.role != "staff":
        return RedirectResponse("/login", status_code=302)

    conversations = db.query(Conversation).filter(
        Conversation.status == "open"
    ).all()

    return templates.TemplateResponse(
        "staff_inbox.html",
        {
            "request": request,
            "user": user,
            "conversations": conversations
        }
    )


# =========================
# VIEW CONVERSATION
# =========================

@router.get("/staff/conversation/{conversation_id}", response_class=HTMLResponse)
def view_conversation(conversation_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request)
    if not user or user.role != "staff":
        return RedirectResponse("/login", status_code=302)

    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id
    ).first()

    if not conversation:
        return RedirectResponse("/staff/inbox", status_code=302)

    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.timestamp).all()

    return templates.TemplateResponse(
        "conversation.html",
        {
            "request": request,
            "user": user,
            "messages": messages,
            "conversation_id": conversation_id
        }
    )


# =========================
# STAFF REPLY
# =========================

@router.post("/staff/reply/{conversation_id}")
async def reply_to_conversation(
    conversation_id: int,
    request: Request,
    message: str = Form(...),
    db: Session = Depends(get_db)
):
    user = get_current_user(request)
    if not user or user.role != "staff":
        return RedirectResponse("/login", status_code=302)

    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id
    ).first()

    if not conversation:
        return RedirectResponse("/staff/inbox", status_code=302)

    # Save message in DB
    db.add(
        Message(
            conversation_id=conversation_id,
            sender="staff",
            body=message
        )
    )
    db.commit()

    # Send via WhatsApp
    await send_whatsapp_message(
        conversation.contact.phone,
        message
    )

    return RedirectResponse(f"/staff/conversation/{conversation_id}", status_code=302)


# =========================
# INVENTORY UPDATE
# =========================

@router.post("/staff/inventory/update")
def update_inventory(
    request: Request,
    item_id: int = Form(...),
    quantity: int = Form(...),
    db: Session = Depends(get_db)
):
    user = get_current_user(request)
    if not user or user.role != "staff":
        return RedirectResponse("/login", status_code=302)

    item = db.query(Inventory).filter(
        Inventory.id == item_id
    ).first()

    if item:
        item.quantity = quantity
        db.commit()

    return RedirectResponse("/staff", status_code=302)
