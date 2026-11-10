"""Two kinds of callers:

- Edge devices (cameras) authenticate with an API key in `X-Device-Key`.
  Keys are generated once, shown once, and stored as a SHA-256 hash.
- Dashboard users log in with username/password and receive a JWT.
"""
import hashlib
import secrets
from datetime import UTC, datetime, timedelta

import bcrypt
from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app.config import Settings
from app.storage.base import Row, Storage

oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_storage(request: Request) -> Storage:
    return request.app.state.storage


# ---- device keys --------------------------------------------------------
def new_device_key() -> tuple[str, str]:
    """Return (plain_key, sha256_hash). The plain key is shown to the user once."""
    key = "fb_" + secrets.token_urlsafe(24)
    return key, hash_device_key(key)


def hash_device_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


def require_device(
    x_device_key: str = Header(..., alias="X-Device-Key"),
    storage: Storage = Depends(get_storage),
) -> Row:
    device = storage.get_device_by_key_hash(hash_device_key(x_device_key))
    if device is None or str(device.get("status", "")).lower() != "active":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid or inactive device key")
    return device


# ---- passwords & JWT ----------------------------------------------------
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    except ValueError:
        return False


def create_token(user: Row, settings: Settings) -> str:
    expires = datetime.now(UTC) + timedelta(minutes=settings.jwt_expires_minutes)
    payload = {"sub": user["username"], "uid": user["user_id"], "role": user.get("role", "operator"), "exp": expires}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def require_user(request: Request, token: str = Depends(oauth2)) -> Row:
    settings: Settings = request.app.state.settings
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as err:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid or expired token",
                            headers={"WWW-Authenticate": "Bearer"}) from err
    return {"user_id": payload["uid"], "username": payload["sub"], "role": payload.get("role", "operator")}


def require_admin(user: Row = Depends(require_user)) -> Row:
    if user["role"] != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "admin role required")
    return user
