def normalize_phone(phone: str) -> str:
    return phone.replace("whatsapp:", "").strip()
