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


def _local_users_map(raw: str | None) -> dict[str, str]:
    """Parse NEXUS_GW_LOCAL_USERS as user:pass,user2:pass2."""
    if not raw or not raw.strip():
        return {}
    out: dict[str, str] = {}
    for part in raw.split(","):
        part = part.strip()
        if not part or ":" not in part:
            continue
        user, _, password = part.partition(":")
        user = user.strip()
        if user:
            out[user] = password
    return out


def _check_local_credentials(username: str, password: str, local_users: str | None) -> bool:
    allow = _local_users_map(local_users)
    if not allow:
        # Lab default: any non-empty credentials
        return bool(username and password)
    return allow.get(username) == password


@router.post("/login", response_model=LoginResponse)
async def login(credentials: LoginRequest):
    """Authenticate and issue JWT token."""
    settings = get_settings()

    # Local auth: lab JWT. OIDC later. Vault AppRole is secrets-only (vault_secrets.py).
    if settings.auth_provider == "local":
        if not _check_local_credentials(
            credentials.username, credentials.password, settings.local_users
        ):
            raise HTTPException(status_code=401, detail="Invalid credentials")
    elif settings.auth_provider == "oidc":
        raise HTTPException(status_code=503, detail="OIDC auth provider not yet implemented")
    else:
        raise HTTPException(status_code=400, detail="Unsupported auth_provider")

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
