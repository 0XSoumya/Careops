from fastapi import APIRouter, Request, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models import Contact, Conversation, Message, Booking
from app.utils.phone import normalize_phone
from app.utils.security import hash_secret_code
from app.services.whatsapp_service import send_whatsapp_message

router = APIRouter()


@router.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request, db: Session = Depends(get_db)):
    form_data = await request.form()

    from_number = form_data.get("From")
    body = form_data.get("Body", "").strip()

    if not from_number:
        return PlainTextResponse("No sender", status_code=400)

    phone = normalize_phone(from_number)

    contact = db.query(Contact).filter(Contact.phone == phone).first()
    if not contact:
        return PlainTextResponse("Unknown contact", status_code=200)

    conversation = db.query(Conversation).filter(
        Conversation.contact_id == contact.id
    ).first()

    if not conversation:
        conversation = Conversation(contact_id=contact.id)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    # Persist inbound message
    message = Message(
        conversation_id=conversation.id,
        sender="client",
        body=body,
    )
    db.add(message)
    db.commit()

    # Check pending booking
    booking = db.query(Booking).filter(
        Booking.contact_id == contact.id,
        Booking.status == "pending"
    ).first()

    if booking:
        incoming_hash = hash_secret_code(body)

        if incoming_hash == booking.secret_code_hash:
            booking.status = "confirmed"
            db.commit()

            await send_whatsapp_message(
                contact.phone,
                "Your booking has been confirmed successfully."
            )
        else:
            await send_whatsapp_message(
                contact.phone,
                "Invalid secret code. Please try again."
            )

    return PlainTextResponse("OK", status_code=200)
