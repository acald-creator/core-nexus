"""In-memory store for factory-agents review approvals (ADR 0009 human gate)."""

from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

_lock = threading.Lock()
_store: dict[str, dict[str, Any]] = {}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def to_console_approval(record: dict[str, Any]) -> dict[str, Any]:
    pr = record.get("pr_number")
    target = record.get("repo") or "unknown"
    if pr:
        target = f"{target}#{pr}"
    return {
        "id": record["id"],
        "sessionId": record.get("head_sha") or record["id"],
        "proposedTool": "factory-agents / review",
        "target": target,
        "argumentsSummary": record.get("summary") or "Factory review needs human review",
        "submittedAt": record.get("submitted_at") or _now_iso(),
        "status": record.get("status") or "pending",
        "source": "factory",
        "riskMax": record.get("risk_max"),
        "checkRunUrl": record.get("check_run_url"),
    }


def create_review_approval(
    *,
    repo: str,
    head_sha: str,
    risk_max: str,
    summary: str,
    pr_number: int | None = None,
    check_run_url: str | None = None,
    findings_count: int = 0,
) -> dict[str, Any]:
    approval_id = f"factory-{uuid4().hex[:12]}"
    record = {
        "id": approval_id,
        "repo": repo,
        "head_sha": head_sha,
        "pr_number": pr_number,
        "check_run_url": check_run_url,
        "risk_max": risk_max,
        "summary": summary,
        "findings_count": findings_count,
        "submitted_at": _now_iso(),
        "status": "pending",
    }
    with _lock:
        _store[approval_id] = record
    return to_console_approval(record)


def list_approvals(status: str | None = "pending") -> list[dict[str, Any]]:
    with _lock:
        records = list(_store.values())
    if status:
        records = [r for r in records if r.get("status") == status]
    records.sort(key=lambda r: r.get("submitted_at", ""))
    return [to_console_approval(r) for r in records]


def submit_decision(
    approval_id: str,
    decision: Literal["approve", "reject"],
) -> dict[str, Any]:
    with _lock:
        record = _store.get(approval_id)
        if record is None:
            raise KeyError("not_found")
        if record.get("status") != "pending":
            raise ValueError("not_pending")
        record["status"] = "approved" if decision == "approve" else "rejected"
        record["decided_at"] = _now_iso()
        return to_console_approval(record)


def is_factory_approval_id(approval_id: str) -> bool:
    return approval_id.startswith("factory-")


def reset_store() -> None:
    """Test helper."""
    with _lock:
        _store.clear()
