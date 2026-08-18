"""Structured request logging middleware."""
import time
import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = structlog.get_logger()

# Paths where we don't log request bodies (security)
SENSITIVE_PATHS = {"/api/v1/auth/login", "/api/v1/auth/refresh"}


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    """Log every request with method, path, status, duration, and user."""

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000

        user_sub = None
        if hasattr(request.state, "user"):
            user_sub = request.state.user.get("sub")

        logger.info(
            "request",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=round(duration_ms, 2),
            client_ip=request.client.host if request.client else None,
            user=user_sub,
        )

        return response
