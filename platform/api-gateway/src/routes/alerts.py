"""Alerts aggregation routes."""
from fastapi import APIRouter, HTTPException, Query, Request

router = APIRouter()


@router.get("/alerts")
async def list_alerts(
    request: Request,
    severity: str | None = None,
    source: str | None = None,
    from_ts: str | None = Query(None, alias="from"),
    to_ts: str | None = Query(None, alias="to"),
    limit: int = Query(100, ge=1, le=500),
):
    """List security alerts from Wazuh with optional filtering."""
    try:
        data = await request.app.state.wazuh_client.get_alerts(
            severity=severity,
            source=source,
            from_ts=from_ts,
            to_ts=to_ts,
            limit=limit,
        )
        alerts = data.get("data", {}).get("affected_items", [])
        total = data.get("data", {}).get("total_affected_items", len(alerts))
        return {"alerts": alerts, "total": total}
    except Exception:
        raise HTTPException(status_code=502, detail="Wazuh API unavailable")


@router.get("/alerts/{alert_id}/triage")
async def get_alert_triage(alert_id: str, request: Request):
    """Get AI triage result for a specific alert."""
    try:
        result = await request.app.state.ai_inference_client.get_triage(alert_id)
        if result is None:
            raise HTTPException(status_code=404, detail="No triage result available")
        return result
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=502, detail="AI Inference service unavailable")
