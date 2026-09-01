"""Approvals routes — list and decision submission."""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Literal

from src.services import factory_approvals

router = APIRouter()


class DecisionRequest(BaseModel):
    decision: Literal["approve", "reject"]


@router.get("/approvals")
async def list_approvals(request: Request, status: str | None = "pending"):
    """List approval actions (Athena OPAR + factory review), defaulting to pending."""
    factory = factory_approvals.list_approvals(status=status)
    try:
        athena = await request.app.state.athena_client.get_approvals(status=status)
    except Exception:
        if factory:
            athena = []
        else:
            raise HTTPException(status_code=502, detail="athena-agents service unavailable")
    merged = factory + athena
    merged.sort(key=lambda a: a.get("submittedAt", ""))
    return merged


@router.post("/approvals/{approval_id}/decision")
async def submit_decision(approval_id: str, body: DecisionRequest, request: Request):
    """Submit an approve/reject decision for a pending action."""
    if factory_approvals.is_factory_approval_id(approval_id):
        try:
            factory_approvals.submit_decision(approval_id, body.decision)
            return {"success": True}
        except KeyError:
            raise HTTPException(status_code=404, detail="Approval not found")
        except ValueError:
            raise HTTPException(status_code=409, detail="Approval no longer pending")

    try:
        await request.app.state.athena_client.submit_decision(
            approval_id=approval_id,
            decision=body.decision,
        )
        return {"success": True}
    except Exception as e:
        if "404" in str(e):
            raise HTTPException(status_code=404, detail="Approval not found")
        if "409" in str(e):
            raise HTTPException(status_code=409, detail="Approval no longer pending")
        raise HTTPException(status_code=502, detail="athena-agents service unavailable")
