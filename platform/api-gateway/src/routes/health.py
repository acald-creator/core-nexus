"""Health check proxy route."""
import time

import httpx
from fastapi import APIRouter, HTTPException

from src.routes.services import _load_registry

router = APIRouter()

HEALTH_TIMEOUT = 5.0


@router.get("/health/{service_id}")
async def check_service_health(service_id: str):
    """Proxy a health check to the configured service endpoint."""
    registry = _load_registry()
    service = next((s for s in registry if s["id"] == service_id), None)

    if not service:
        raise HTTPException(status_code=404, detail=f"Service not found: {service_id}")

    health_endpoint = service.get("healthEndpoint")
    if not health_endpoint:
        return {"serviceId": service_id, "status": "unknown", "statusCode": None, "responseTimeMs": None}

    url = f"{service['url']}{health_endpoint}"
    start = time.perf_counter()

    try:
        async with httpx.AsyncClient(verify=False, timeout=HEALTH_TIMEOUT) as client:
            response = await client.get(url)
        elapsed = (time.perf_counter() - start) * 1000

        status = "healthy" if response.is_success else "degraded"
        return {
            "serviceId": service_id,
            "status": status,
            "statusCode": response.status_code,
            "responseTimeMs": round(elapsed, 2),
        }
    except httpx.TimeoutException:
        elapsed = (time.perf_counter() - start) * 1000
        return {
            "serviceId": service_id,
            "status": "timeout",
            "statusCode": None,
            "responseTimeMs": round(elapsed, 2),
        }
    except httpx.ConnectError:
        return {
            "serviceId": service_id,
            "status": "offline",
            "statusCode": None,
            "responseTimeMs": None,
        }
