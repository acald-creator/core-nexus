"""Alerts aggregation routes."""
from __future__ import annotations

import httpx
from fastapi import APIRouter, HTTPException, Query, Request

from src.models.alerts import AlertsResponse, TriageResponse
from src.services.alerts import (
    clamp_limit,
    filter_alerts,
    map_triage_alert,
    map_wazuh_alert,
)

router = APIRouter()


async def _list_wazuh_alerts(
    request: Request,
    *,
    severity: str | None,
    source: str | None,
    from_ts: str | None,
    to_ts: str | None,
    limit: int,
) -> list:
    data = await request.app.state.wazuh_client.get_alerts(
        severity=severity,
        source=source,
        from_ts=from_ts,
        to_ts=to_ts,
        limit=limit,
    )
    raw_items = data.get("data", {}).get("affected_items", [])
    if not isinstance(raw_items, list):
        raw_items = []
    mapped = [map_wazuh_alert(item) for item in raw_items if isinstance(item, dict)]
    return filter_alerts(
        mapped,
        severity=severity,
        source=source,
        from_ts=from_ts,
        to_ts=to_ts,
    )


async def _list_triage_alerts(
    request: Request,
    *,
    severity: str | None,
    source: str | None,
    from_ts: str | None,
    to_ts: str | None,
    limit: int,
) -> list:
    records = await request.app.state.ai_inference_client.list_triage(limit=limit)
    mapped = [map_triage_alert(item) for item in records]
    return filter_alerts(
        mapped,
        severity=severity,
        source=source,
        from_ts=from_ts,
        to_ts=to_ts,
    )


@router.get("/alerts", response_model=AlertsResponse)
async def list_alerts(
    request: Request,
    severity: str | None = None,
    source: str | None = None,
    from_ts: str | None = Query(None, alias="from"),
    to_ts: str | None = Query(None, alias="to"),
    limit: int = Query(100, ge=1, le=500),
):
    """List security alerts for the Console (Wazuh and/or ai-inference triage)."""
    limit = clamp_limit(limit)
    settings = request.app.state.settings
    mode = getattr(settings, "alerts_source", "auto")

    if mode == "triage":
        try:
            filtered = await _list_triage_alerts(
                request,
                severity=severity,
                source=source,
                from_ts=from_ts,
                to_ts=to_ts,
                limit=limit,
            )
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="AI Inference triage timed out")
        except Exception:
            raise HTTPException(status_code=502, detail="AI Inference service unavailable")
        limited = filtered[:limit]
        return AlertsResponse(alerts=limited, total=len(filtered))

    if mode == "wazuh":
        try:
            filtered = await _list_wazuh_alerts(
                request,
                severity=severity,
                source=source,
                from_ts=from_ts,
                to_ts=to_ts,
                limit=limit,
            )
        except Exception:
            raise HTTPException(status_code=502, detail="Wazuh API unavailable")
        limited = filtered[:limit]
        return AlertsResponse(alerts=limited, total=len(filtered))

    # auto: prefer Wazuh; fall back to triage store (hybrid-sensor / ADR 0011)
    try:
        filtered = await _list_wazuh_alerts(
            request,
            severity=severity,
            source=source,
            from_ts=from_ts,
            to_ts=to_ts,
            limit=limit,
        )
        limited = filtered[:limit]
        return AlertsResponse(alerts=limited, total=len(filtered))
    except Exception:
        try:
            filtered = await _list_triage_alerts(
                request,
                severity=severity,
                source=source,
                from_ts=from_ts,
                to_ts=to_ts,
                limit=limit,
            )
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="AI Inference triage timed out")
        except Exception:
            raise HTTPException(status_code=502, detail="Wazuh and AI Inference unavailable")
        limited = filtered[:limit]
        return AlertsResponse(alerts=limited, total=len(filtered))


@router.get("/alerts/{alert_id}/triage", response_model=TriageResponse)
async def get_alert_triage(alert_id: str, request: Request):
    """Get AI triage for an alert — persisted lookup, else score from Wazuh payload."""
    client = request.app.state.ai_inference_client
    try:
        result = await client.get_triage(alert_id)
        if result is None:
            # E0 fallback: find alert in recent Wazuh window and POST for scoring.
            raw_match: dict | None = None
            try:
                data = await request.app.state.wazuh_client.get_alerts(limit=200)
                raw_items = data.get("data", {}).get("affected_items", [])
                if isinstance(raw_items, list):
                    for item in raw_items:
                        if not isinstance(item, dict):
                            continue
                        rid = str(item.get("id") or item.get("_id") or item.get("alert_id") or "")
                        if rid == alert_id:
                            raw_match = item
                            break
            except Exception:
                raw_match = None

            if raw_match is not None:
                result = await client.create_triage(raw_match)
            else:
                raise HTTPException(status_code=404, detail="No triage result available")
    except HTTPException:
        raise
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="AI Inference triage timed out")
    except Exception:
        raise HTTPException(status_code=502, detail="AI Inference service unavailable")

    try:
        return TriageResponse.model_validate(result)
    except Exception:
        raise HTTPException(status_code=502, detail="AI Inference returned invalid triage payload")
