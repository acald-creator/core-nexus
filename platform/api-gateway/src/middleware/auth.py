"""JWT authentication middleware."""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
import jwt

from src.config import get_settings

PUBLIC_PATHS = {
    "/api/v1/auth/login",
    "/api/v1/factory/reviews",
    "/healthz",
    "/readyz",
    "/docs",
    "/openapi.json",
}


class JWTAuthMiddleware(BaseHTTPMiddleware):
    """Validate JWT on all requests except public paths and OPTIONS."""

    async def dispatch(self, request: Request, call_next):
        if request.url.path in PUBLIC_PATHS or request.method == "OPTIONS":
            return await call_next(request)

        token = self._extract_token(request)
        if not token:
            return JSONResponse(
                status_code=401,
                content={"error": "Missing authentication token", "code": "AUTH_TOKEN_MISSING"},
            )

        settings = get_settings()
        try:
            payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
            request.state.user = payload
        except jwt.ExpiredSignatureError:
            return JSONResponse(
                status_code=401,
                content={"error": "Token has expired", "code": "AUTH_TOKEN_EXPIRED"},
            )
        except jwt.InvalidTokenError:
            return JSONResponse(
                status_code=401,
                content={"error": "Invalid authentication token", "code": "AUTH_TOKEN_INVALID"},
            )

        return await call_next(request)

    def _extract_token(self, request: Request) -> str | None:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return auth_header[7:]
        # SSE fallback: token in query param
        return request.query_params.get("token")
