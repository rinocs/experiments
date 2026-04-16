"""
JWT Auth — FastAPI dependency injection.
- POST /auth/token  →  emette JWT (username+password)
- Dependency `get_current_user` protegge tutti gli endpoint sensibili
- Utenti in-memory per ora; sostituisci con DB a piacere
"""
import os, time
from typing import Annotated
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-in-prod-use-openssl-rand-hex-32")
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# ── utenti in-memory (sostituire con DB) ───────────────────────────────────
USERS_DB: dict[str, dict] = {
    "admin": {"username": "admin", "hashed_pw": pwd_ctx.hash("admin"), "role": "admin"},
    "readonly": {"username": "readonly", "hashed_pw": pwd_ctx.hash("readonly"), "role": "reader"},
}

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = TOKEN_EXPIRE_MINUTES * 60

class UserPayload(BaseModel):
    username: str
    role: str


def _verify(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)


def _create_token(data: dict) -> str:
    payload = {**data, "exp": datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRE_MINUTES)}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def issue_token(form: OAuth2PasswordRequestForm) -> TokenResponse:
    user = USERS_DB.get(form.username)
    if not user or not _verify(form.password, user["hashed_pw"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenziali errate")
    token = _create_token({"sub": user["username"], "role": user["role"]})
    return TokenResponse(access_token=token)


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> UserPayload:
    exc = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token non valido",
                        headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        role = payload.get("role", "reader")
        if not username:
            raise exc
        return UserPayload(username=username, role=role)
    except JWTError:
        raise exc


def require_admin(user: Annotated[UserPayload, Depends(get_current_user)]) -> UserPayload:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Richiede ruolo admin")
    return user
