"""Factory AI webhook routes — review findings into Console Approvals."""

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, Field

from src.config import get_settings
from src.services import factory_approvals

router = APIRouter()

HIGH_RISK = {"high", "critical"}


class FactoryFinding(BaseModel):
    id: str = ""
    title: str = ""
    risk: str = "informational"
    path: str | None = None
    line: int | None = None
    rationale: str = ""


class FactoryReviewWebhook(BaseModel):
    repo: str = Field(min_length=3)
    head_sha: str = Field(min_length=7)
    risk_max: str
    summary: str
    pr_number: int | None = None
    check_run_url: str | None = None
    findings: list[FactoryFinding] = Field(default_factory=list)


def _validate_webhook_token(request: Request, token_header: str | None) -> None:
    settings = get_settings()
    expected = settings.factory_webhook_token
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="Factory webhook not configured (set NEXUS_GW_FACTORY_WEBHOOK_TOKEN)",
        )
    provided = token_header or request.headers.get("X-Factory-Webhook-Token")
    if not provided or provided != expected:
        raise HTTPException(status_code=401, detail="Invalid factory webhook token")


@router.post("/factory/reviews")
async def ingest_factory_review(
    body: FactoryReviewWebhook,
    request: Request,
    authorization: str | None = Header(default=None),
):
    """
    Ingest a high-risk factory-agents review for Console Approvals.

    Auth: Bearer token or X-Factory-Webhook-Token matching NEXUS_GW_FACTORY_WEBHOOK_TOKEN.
    """
    bearer = None
    if authorization and authorization.startswith("Bearer "):
        bearer = authorization[7:]
    _validate_webhook_token(request, bearer)

    if body.risk_max not in HIGH_RISK:
        return {
            "accepted": False,
            "reason": "risk_below_threshold",
            "risk_max": body.risk_max,
        }

    approval = factory_approvals.create_review_approval(
        repo=body.repo,
        head_sha=body.head_sha,
        pr_number=body.pr_number,
        check_run_url=body.check_run_url,
        risk_max=body.risk_max,
        summary=body.summary,
        findings_count=len(body.findings),
    )
    return {"accepted": True, "approval": approval}
