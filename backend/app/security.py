import os

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError
from fastapi import HTTPException, Request
from itsdangerous import BadSignature, URLSafeTimedSerializer

COOKIE = "samick_admin"

def signer():
    secret = os.getenv("SESSION_SECRET", "")
    if len(secret) < 24:
        raise HTTPException(503, "SESSION_SECRET belum diatur atau terlalu pendek")
    return URLSafeTimedSerializer(secret, salt="samick-demo-session")

def verify_password(password: str) -> bool:
    hashed = os.getenv("ADMIN_PASSWORD_HASH", "")
    if not hashed:
        raise HTTPException(503, "ADMIN_PASSWORD_HASH belum diatur")
    try:
        return PasswordHasher().verify(hashed, password)
    except (VerifyMismatchError, VerificationError):
        return False

def require_admin(request: Request):
    value = request.cookies.get(COOKIE)
    if not value:
        raise HTTPException(401, "Silakan login sebagai admin")
    try:
        username = signer().loads(value, max_age=60 * 60 * 8)
    except BadSignature:
        raise HTTPException(401, "Sesi admin tidak valid atau kedaluwarsa")
    if username != os.getenv("ADMIN_USERNAME", "admin"):
        raise HTTPException(401, "Sesi admin tidak valid")
    return username
