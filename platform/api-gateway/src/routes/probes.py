"""Health and readiness probes."""
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/healthz")
async def health_check():
    """Liveness probe — returns 200 if process is running."""
    return {"status": "ok"}


@router.get("/readyz")
async def readiness_check(request: Request):
    """Readiness probe — verifies upstream connectivity."""
    checks = {}

    # Check Wazuh
    try:
        await request.app.state.wazuh_client.authenticate()
        checks["wazuh"] = "ok"
    except Exception:
        checks["wazuh"] = "unreachable"

    # Check MinIO
    try:
        request.app.state.minio_client.bucket_exists()
        checks["minio"] = "ok"
    except Exception:
        checks["minio"] = "unreachable"

    all_ok = all(v == "ok" for v in checks.values())
    return JSONResponse(
        status_code=200 if all_ok else 503,
        content={"status": "ready" if all_ok else "not_ready", "checks": checks},
    )
