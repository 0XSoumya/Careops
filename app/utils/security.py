import bcrypt
import hashlib
from app.config import SECRET_CODE_SALT


# Password hashing (for users)
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


# Secret code hashing (for bookings)
def hash_secret_code(code: str) -> str:
    return hashlib.sha256((code + SECRET_CODE_SALT).encode()).hexdigest()
