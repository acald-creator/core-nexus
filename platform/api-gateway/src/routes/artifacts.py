"""Artifacts routes — list and download URL generation from MinIO."""
from fastapi import APIRouter, HTTPException, Query, Request
from typing import Literal

router = APIRouter()

ArtifactCategory = Literal["pcaps", "sboms", "skills", "sessions"]

CATEGORY_PREFIXES: dict[str, str] = {
    "pcaps": "pcaps/",
    "sboms": "sboms/",
    "skills": "skills/",
    "sessions": "sessions/",
}


@router.get("/artifacts")
async def list_artifacts(
    request: Request,
    category: ArtifactCategory = Query(..., description="Artifact category"),
):
    """List artifact objects by category from MinIO."""
    prefix = CATEGORY_PREFIXES[category]
    try:
        objects = request.app.state.minio_client.list_objects(prefix=prefix)
        for obj in objects:
            obj["category"] = category
        return objects
    except Exception:
        raise HTTPException(status_code=502, detail="MinIO unavailable")


@router.get("/artifacts/{key:path}/download-url")
async def get_download_url(key: str, request: Request):
    """Generate a pre-signed MinIO download URL (15 min expiry)."""
    try:
        url = request.app.state.minio_client.get_presigned_url(key, expires_minutes=15)
        return {"url": url}
    except Exception:
        raise HTTPException(status_code=404, detail=f"Artifact not found: {key}")
