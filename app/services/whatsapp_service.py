import httpx
from app.config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER
import logging

logger = logging.getLogger(__name__)

async def send_whatsapp_message(to: str, body: str):
    if not TWILIO_ACCOUNT_SID:
        logger.warning("Twilio not configured.")
        return

    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json",
                data={
                    "From": f"whatsapp:{TWILIO_WHATSAPP_NUMBER}",
                    "To": f"whatsapp:{to}",
                    "Body": body
                },
                auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            )
    except Exception as e:
        logger.error(f"Twilio send failed: {e}")
