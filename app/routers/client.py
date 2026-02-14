from fastapi import APIRouter, Form, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import secrets

from app.database import get_db
from app.models import (
    Contact,
    Conversation,
    Ticket,
    Booking,
    Workspace,
    Message,
)
from app.utils.phone import normalize_phone
from app.utils.security import hash_secret_code
from app.services.whatsapp_service import send_whatsapp_message


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def generate_ticket_number():
    return f"TCK-{secrets.token_hex(4).upper()}"


def generate_secret_code():
    return str(secrets.randbelow(900000) + 100000)


def validate_booking_time(workspace: Workspace, date_str: str, time_str: str):
    local_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")

    active_days = [d.strip() for d in workspace.active_days.split(",")]
    weekday = local_dt.strftime("%a")

    if weekday not in active_days:
        return None

    start_hour = datetime.strptime(workspace.active_hours_start, "%H:%M").time()
    end_hour = datetime.strptime(workspace.active_hours_end, "%H:%M").time()

    if not (start_hour <= local_dt.time() <= end_hour):
        return None

    return local_dt


@router.get("/client", response_class=HTMLResponse)
def client_home(request: Request):
    return templates.TemplateResponse(
        "client_dashboard.html",
        {"request": request}
    )


def get_or_create_contact(db: Session, name: str, phone: str):
    phone = normalize_phone(phone)
    contact = db.query(Contact).filter(Contact.phone == phone).first()

    if not contact:
        contact = Contact(name=name, phone=phone)
        db.add(contact)
        db.commit()
        db.refresh(contact)

    return contact


def get_or_create_conversation(db: Session, contact: Contact):
    convo = db.query(Conversation).filter(
        Conversation.contact_id == contact.id
    ).first()

    if not convo:
        convo = Conversation(contact_id=contact.id)
        db.add(convo)
        db.commit()
        db.refresh(convo)

    return convo


@router.post("/client/query")
async def submit_query(
    name: str = Form(...),
    phone: str = Form(...),
    message: str = Form(...),
    db: Session = Depends(get_db),
):
    contact = get_or_create_contact(db, name, phone)
    convo = get_or_create_conversation(db, contact)

    db.add(
        Message(
            conversation_id=convo.id,
            sender="client",
            body=message,
        )
    )

    ticket_number = generate_ticket_number()

    ticket = Ticket(
        ticket_number=ticket_number,
        form_type="query",
        contact_id=contact.id,
        conversation_id=convo.id,
    )
    db.add(ticket)
    db.commit()

    await send_whatsapp_message(
        contact.phone,
        f"Your query ticket number is {ticket_number}. We will contact you shortly.",
    )

    return RedirectResponse("/client", status_code=302)


@router.post("/client/booking")
async def submit_booking(
    name: str = Form(...),
    phone: str = Form(...),
    service_type: str = Form(...),
    date: str = Form(...),
    time: str = Form(...),
    db: Session = Depends(get_db),
):
    workspace = db.query(Workspace).first()
    if not workspace:
        return RedirectResponse("/client", status_code=302)

    valid_time = validate_booking_time(workspace, date, time)
    if not valid_time:
        return HTMLResponse("Invalid booking time.")

    contact = get_or_create_contact(db, name, phone)
    convo = get_or_create_conversation(db, contact)

    ticket_number = generate_ticket_number()

    ticket = Ticket(
        ticket_number=ticket_number,
        form_type="booking",
        contact_id=contact.id,
        conversation_id=convo.id,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    secret_code = generate_secret_code()
    hashed_code = hash_secret_code(secret_code)

    end_time = valid_time + timedelta(
        minutes=workspace.default_service_duration_minutes
    )

    booking = Booking(
        ticket_id=ticket.id,
        contact_id=contact.id,
        service_type=service_type,
        start_time=valid_time,
        end_time=end_time,
        secret_code_hash=hashed_code,
    )
    db.add(booking)
    db.commit()

    await send_whatsapp_message(
        contact.phone,
        f"Booking created. Ticket: {ticket_number}. "
        f"Your secret code is {secret_code}. Send this via WhatsApp to confirm.",
    )

    return RedirectResponse("/client", status_code=302)


@router.post("/client/feedback")
async def submit_feedback(
    name: str = Form("Anonymous"),
    phone: str = Form(...),
    rating: int = Form(...),
    feedback: str = Form(...),
    db: Session = Depends(get_db),
):
    contact = get_or_create_contact(db, name, phone)
    convo = get_or_create_conversation(db, contact)

    ticket_number = generate_ticket_number()

    ticket = Ticket(
        ticket_number=ticket_number,
        form_type="feedback",
        contact_id=contact.id,
        conversation_id=convo.id,
    )
    db.add(ticket)
    db.commit()

    await send_whatsapp_message(
        contact.phone,
        f"Thank you for your feedback. Ticket: {ticket_number}",
    )

    return RedirectResponse("/client", status_code=302)
