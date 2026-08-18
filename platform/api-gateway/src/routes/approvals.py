"""Approvals routes — list and decision submission."""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Literal

router = APIRouter()


class DecisionRequest(BaseModel):
    decision: Literal["approve", "reject"]


@router.get("/approvals")
async def list_approvals(request: Request, status: str | None = "pending"):
    """List approval actions, defaulting to pending."""
    try:
        approvals = await request.app.state.athena_client.get_approvals(status=status)
        # Sort by submittedAt ascending (oldest first)
        approvals.sort(key=lambda a: a.get("submittedAt", ""))
        return approvals
    except Exception:
        raise HTTPException(status_code=502, detail="athena-agents service unavailable")


@router.post("/approvals/{approval_id}/decision")
async def submit_decision(approval_id: str, body: DecisionRequest, request: Request):
    """Submit an approve/reject decision for a pending action."""
    try:
        result = await request.app.state.athena_client.submit_decision(
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
