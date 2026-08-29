"""Authentication routes — login and refresh."""
from datetime import datetime, timezone, timedelta

import jwt
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from src.config import get_settings

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    expires_at: str


@router.post("/login", response_model=LoginResponse)
async def login(credentials: LoginRequest):
    """Authenticate and issue JWT token."""
    settings = get_settings()

    # Local auth: lab JWT (production would use OIDC). Vault AppRole is for
    # secrets hydrate only — see vault_secrets.py — not user login.
    if settings.auth_provider == "local":
        if not credentials.username or not credentials.password:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    else:
        # Vault/OIDC user auth not implemented; keep auth_provider=local for labs
        raise HTTPException(status_code=503, detail="Vault auth provider not yet implemented")

    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=settings.jwt_expiration_minutes)

    payload = {
        "sub": credentials.username,
        "role": "analyst",
        "iat": now,
        "exp": exp,
    }

    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

    return LoginResponse(token=token, expires_at=exp.isoformat())


@router.post("/refresh", response_model=LoginResponse)
async def refresh_token(request: Request):
    """Refresh a valid non-expired token."""
    settings = get_settings()

    if not hasattr(request.state, "user"):
        raise HTTPException(status_code=401, detail="No valid token to refresh")

    user = request.state.user
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=settings.jwt_expiration_minutes)

    payload = {
        "sub": user["sub"],
        "role": user.get("role", "analyst"),
        "iat": now,
        "exp": exp,
    }

    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

    return LoginResponse(token=token, expires_at=exp.isoformat())
