import os
from datetime import datetime, timedelta, timezone
from jose import jwt

SECRET_KEY = os.getenv("JWT_SECRET", "supersecretjwtkey-module13-is601-changeme")
ALGORITHM = "HS256"
EXPIRE_MINUTES = 30


def create_token(user_id: int, email: str) -> str:
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=EXPIRE_MINUTES),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
