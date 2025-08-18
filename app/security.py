import os
import time
from typing import Optional

import jwt
from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_secret_key() -> str:
    return os.getenv("SECRET_KEY", "dev-secret-change-me")


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def create_access_token(subject: str, expires_in_seconds: int = 60 * 60 * 24) -> str:
    now = int(time.time())
    payload = {"sub": subject, "iat": now, "exp": now + expires_in_seconds}
    token = jwt.encode(payload, get_secret_key(), algorithm="HS256")
    return token


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, get_secret_key(), algorithms=["HS256"])
        return payload
    except jwt.PyJWTError:
        return None


