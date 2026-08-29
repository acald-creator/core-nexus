"""Artifact/run metadata index (D1 via nexus-metadata Worker)."""
from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

router = APIRouter()

Category = Literal["pcaps", "sboms", "skills", "sessions", "images", "other"]


class ArtifactIndexBody(BaseModel):
    object_key: str
    category: Category
    digest: str | None = None
    media_type: str | None = None
    size_bytes: int | None = None
    source: str = "gateway"
    image_ref: str | None = None
    ssf_attestation_url: str | None = None
    metadata_json: dict[str, Any] | None = None


class RunBody(BaseModel):
    kind: str = Field(..., min_length=1)
    status: str = "pending"
    actor: str | None = None
    summary: str | None = None
    metadata_json: dict[str, Any] | None = None


def _client(request: Request):
    client = getattr(request.app.state, "metadata_index", None)
    if client is None or not client.enabled:
        raise HTTPException(status_code=503, detail="metadata index not configured")
    return client


@router.get("/artifact-index")
async def list_indexed_artifacts(
    request: Request,
    category: Category | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    """List provenance rows from D1 (not R2 object listing)."""
    try:
        return await _client(request).list_artifacts(category=category, limit=limit)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=502, detail="metadata index unavailable")


@router.post("/artifact-index", status_code=201)
async def upsert_indexed_artifact(body: ArtifactIndexBody, request: Request):
    """Register or update an artifact metadata row (blob must already be on R2/MinIO)."""
    try:
        return await _client(request).upsert_artifact(body.model_dump(exclude_none=True))
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=502, detail="metadata index unavailable")


@router.post("/runs", status_code=201)
async def create_run(body: RunBody, request: Request):
    try:
        return await _client(request).create_run(body.model_dump(exclude_none=True))
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=502, detail="metadata index unavailable")


@router.get("/runs/{run_id}")
async def get_run(run_id: str, request: Request):
    try:
        return await _client(request).get_run(run_id)
    except HTTPException:
        raise
    except Exception as exc:
        if getattr(exc, "response", None) is not None and exc.response.status_code == 404:
            raise HTTPException(status_code=404, detail="run not found")
        raise HTTPException(status_code=502, detail="metadata index unavailable")
