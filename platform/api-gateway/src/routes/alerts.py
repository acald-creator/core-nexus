"""Alerts aggregation routes."""
from __future__ import annotations

import httpx
from fastapi import APIRouter, HTTPException, Query, Request

from src.models.alerts import AlertsResponse, TriageResponse
from src.services.alerts import clamp_limit, filter_alerts, map_wazuh_alert

router = APIRouter()


@router.get("/alerts", response_model=AlertsResponse)
async def list_alerts(
    request: Request,
    severity: str | None = None,
    source: str | None = None,
    from_ts: str | None = Query(None, alias="from"),
    to_ts: str | None = Query(None, alias="to"),
    limit: int = Query(100, ge=1, le=500),
):
    """List security alerts from Wazuh, mapped to SOCAlert for the Console."""
    limit = clamp_limit(limit)
    try:
        data = await request.app.state.wazuh_client.get_alerts(
            severity=severity,
            source=source,
            from_ts=from_ts,
            to_ts=to_ts,
            limit=limit,
        )
    except Exception:
        raise HTTPException(status_code=502, detail="Wazuh API unavailable")

    raw_items = data.get("data", {}).get("affected_items", [])
    if not isinstance(raw_items, list):
        raw_items = []

    mapped = [map_wazuh_alert(item) for item in raw_items if isinstance(item, dict)]
    filtered = filter_alerts(
        mapped,
        severity=severity,
        source=source,
        from_ts=from_ts,
        to_ts=to_ts,
    )
    limited = filtered[:limit]
    return AlertsResponse(alerts=limited, total=len(filtered))


@router.get("/alerts/{alert_id}/triage", response_model=TriageResponse)
async def get_alert_triage(alert_id: str, request: Request):
    """Get AI triage result for a specific alert."""
    try:
        result = await request.app.state.ai_inference_client.get_triage(alert_id)
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="AI Inference triage timed out")
    except Exception:
        raise HTTPException(status_code=502, detail="AI Inference service unavailable")

    if result is None:
        raise HTTPException(status_code=404, detail="No triage result available")

    try:
        return TriageResponse.model_validate(result)
    except Exception:
        raise HTTPException(status_code=502, detail="AI Inference returned invalid triage payload")
